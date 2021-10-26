# Module to run basic automated OWASP ZAP scan
import argparse
import json
import os
import re
import time
from time import sleep

import progressbar
import requests
import yaml
from zapv2 import ZAPv2


class ZAP_SCAN:
    def __init__(self, proxy_port):
        self.zap = ZAPv2(apikey=os.environ['ZAPTOKEN'], proxies={'http': 'http://127.0.0.1:{}'.format(proxy_port), 'https': 'https://127.0.0.1:{}'.format(proxy_port)})

    def __zap_spider(self, target):
        scan_id = self.zap.spider.scan(target)

        bar = progressbar.ProgressBar(maxval=100, widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage()])
        print('\033[1m', "[*] Start spider module ...", '\033[0m')
        bar.start()
        while int(self.zap.spider.status(scan_id)) < 100:
            time.sleep(1)
            bar.update(int(self.zap.spider.status(scan_id)))
        bar.finish()

        urls = self.zap.spider.results()

        for i in range(0, len(urls)):
            url = str(urls[i])
            if 'ZAP' in url:
                url = url.replace('ZAP', 'ZAP_SCAN')
            urls[i] = url

        return urls

    def __zap_scanner(self, target):
        scan_id = self.zap.ascan.scan(target)

        bar = progressbar.ProgressBar(maxval=100, widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage()])
        print('\033[1m', "[*] Start scan module ...", '\033[0m')
        bar.start()
        while int(self.zap.ascan.status(scan_id)) < 100:
            time.sleep(3)
            bar.update(int(self.zap.ascan.status(scan_id)))
        bar.finish()

        alerts = list()
        for i in self.zap.core.alerts():
            if 'alert' in i and 'url' in i:
                alert = str(i['alert'])
                url = str(i['url'])

                if 'ZAP' in url:
                    url = url.replace('ZAP', 'ZAP_SCAN')

                alerts.append(
                    {
                        'alert': alert,
                        'url': url,
                        'attack': str(i['attack']),
                        'confidence': str(i['confidence']),
                        'cweid': str(i['cweid']),
                        'description': str(i['description']),
                        'evidence': str(i['evidence']),
                        'method': str(i['method']),
                        'name': str(i['name']),
                        'other': str(i['other']),
                        'param': str(i['param']),
                        'risk': str(i['risk']),
                        'solution': str(i['solution']),
                        'wascid': str(i['wascid'])
                    }
                )

        results = {
            'hosts: ': ', '.join(self.zap.core.hosts),
            'number_of_vulnerability': str(len(self.zap.core.alerts())),
            'results': alerts
        }

        return results

    def start_spider_and_scan(self, target):
        if "ZAP Error [java.net.NoRouteToHostException]: No route to host (Host unreachable)" in self.zap.urlopen(target):
            return {"error": "Host unreachable"}

        urls = self.__zap_spider(target)
        results = self.__zap_scanner(target)
        results['urls'] = urls

        return results

    def start_spider(self, target):
        if "ZAP Error [java.net.NoRouteToHostException]: No route to host (Host unreachable)" in self.zap.urlopen(target):
            return {"error": "Host unreachable"}

        return {"urls": self.__zap_spider(target)}

    def domain_urls(self, target):
        raw_urls = self.start_spider(target)
        urls = raw_urls['urls']
        clean_url = []
        for urla in urls:
            ura = re.sub("\?account_name.*", "",  urla)
            urb = re.sub("embed.*", "",  ura)
            urc = re.sub(".*wp\-.*", "",  urb)
            urd = re.sub(".*\.php", "",  urc)
            ure = re.sub(".*\.txt", "",  urd)
            urf = re.sub(".*\.xml", "",  ure)
            url = re.sub(".*rsd", "",  urf)
            clean_url.append(url)
        uniq_urls = list(set(filter(None, clean_url)))

        return uniq_urls

    def seo_migration_analysis(self, target):
        domain_urls = self.domain_urls(target)
        urlen = len(domain_urls)
        base_url = "https://DOMAIN.com"
        index = base_url.index("KEYWORD")
        not_found = list()
        for url in domain_urls:
            req = requests.get(url, allow_redirects=True)
            staging_url = "{}{}{}".format(req.url[:index], "SUBDOMAIN.", req.url[index:])
            staging_req = requests.get(staging_url, allow_redirects=True)
            print(staging_req.url)
            if req.status_code == 404:
                not_found.append(url)

        return not_found


def logo():
    my_log = """
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

    ▒███████▒ ▄▄▄       ██▓███    ██████  ▄████▄   ▄▄▄       ███▄    █
    ▒ ▒ ▒ ▄▀░▒████▄    ▓██░  ██▒▒██    ▒ ▒██▀ ▀█  ▒████▄     ██ ▀█   █
    ░ ▒ ▄▀▒░ ▒██  ▀█▄  ▓██░ ██▓▒░ ▓██▄   ▒▓█    ▄ ▒██  ▀█▄  ▓██  ▀█ ██▒
      ▄▀▒   ░░██▄▄▄▄██ ▒██▄█▓▒ ▒  ▒   ██▒▒▓▓▄ ▄██▒░██▄▄▄▄██ ▓██▒  ▐▌██▒
    ▒███████▒ ▓█   ▓██▒▒██▒ ░  ░▒██████▒▒▒ ▓███▀ ░ ▓█   ▓██▒▒██░   ▓██░
    ░▒▒ ▓░▒░▒ ▒▒   ▓▒█░▒▓▒░ ░  ░▒ ▒▓▒ ▒ ░░ ░▒ ▒  ░ ▒▒   ▓▒█░░ ▒░   ▒ ▒
    ░░▒ ▒ ░ ▒  ▒   ▒▒ ░░▒ ░     ░ ░▒  ░ ░  ░  ▒     ▒   ▒▒ ░░ ░░   ░ ▒░
    ░ ░ ░ ░ ░  ░   ▒   ░░       ░  ░  ░  ░          ░   ▒      ░   ░ ░
      ░ ░          ░  ░               ░  ░ ░            ░  ░         ░
    ░                                    ░                               
                                                        
                    owner: Majid Iranpour
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
"""
    print('\033[92m', my_log, '\033[0m')


def save_to_json(data, file):
    try:
        with open(file, 'w') as outfile:
            json.dump(data, outfile)
    except Exception as e:
        print('\033[93m', e, '\033[0m')


def get_args():
    parser = argparse.ArgumentParser(prog="zap_scan",
                                     usage=logo(),
                                     description="This script spider and scan your target whit OWASP-Zap API")
    parser.add_argument('-u', action='store', help='A target URI', required=True, dest='url')
    parser.add_argument('-o', action='store', help='Save output as JSON in a file', dest='output')
    parser.add_argument('--scan', action='store_true', default=False, help='Scan a target', dest='scan')
    parser.add_argument('--spider', action='store_true', default=False, help='Spider a target', dest='spider')
    parser.add_argument('--port', action='store', type=str, help='ZAP Proxy Port [Default "127.0.0.1:8090"]', dest='proxy_port', default='8090')
    parser.add_argument('--seo', action='store_true', default=False, help='Analyse URIs migration')

    return parser.parse_args()


def main(args):
    if not os.environ['OP_SESSION_my']:
        print('\033[93m', "[Error] Log in 1Password CLI", '\033[0m')
        exit()

    if not args.scan and not args.spider and not args.seo:
        print('\033[93m', "[Error] Select '--scan' or '--spider' or '--seo'", '\033[0m')
        exit()

    elif args.scan:
        zap_class = ZAP_SCAN(args.proxy_port)
        result = zap_class.start_spider_and_scan(args.url)
        if args.output:
            save_to_json(result, args.output)
        else:
            print(json.dumps(result, indent=4))

    elif args.spider:
        zap_class = ZAP_SCAN(args.proxy_port)
        result = zap_class.start_spider(args.url)
        if args.output:
            save_to_json(result, args.output)
        else:
            print(json.dumps(result, indent=4))

    elif args.seo:
        zap_class = ZAP_SCAN(args.proxy_port)
        broken_urls = zap_class.seo_migration_analysis(args.url)
        print("#############")
        print("     404     ")
        print("#############")
        for url in broken_urls:
            print(url)


if __name__ == '__main__':
    args = get_args()
    main(args)
