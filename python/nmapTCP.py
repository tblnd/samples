# Module for a nmap TCP ports scan of known hosts
import logging
import multiprocessing
import os
import shlex
import subprocess
from datetime import datetime

TIMESTAMP = datetime.now().strftime("%Y-%m-%d_%H:%M")


class Scanner:

    # Execute bash command
    def exec_cmd(self, cmd_str):
        args = shlex.split(cmd_str)
        pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = pipe.communicate()
        os.system('stty sane')

    # nmap TCP ports scan
    def port_scan_tcp(self, dc):
        logging.info("Thread %s: starting nmap scan", dc)
        self.exec_cmd("nmap -n -Pn -sT -p- -T4 --min-rate 10000 --initial-rtt-timeout 100ms --min-rtt-timeout 200ms --max-rtt-timeout 400ms --max-retries 2 --min-hostgroup 100 -oX {}_tcp_{}.xml -iL dc/{}.txt".format(dc, TIMESTAMP, dc))
        self.exec_cmd("xsltproc {}_tcp_{}.xml -o {}_tcp_{}.html".format(dc, TIMESTAMP, dc, TIMESTAMP))
        self.exec_cmd("rm {}_tcp_{}.xml".format(dc, TIMESTAMP))
        logging.info("Thread %s: nmap scan completed", dc)


def main():
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")
    DCs = ('dc1', 'dc2', 'dc3', 'dc4')
    posture = Scanner()
    logging.info("Starting scan")
    with multiprocessing.Pool(processes=4) as pool:
        pool.map(posture.port_scan_tcp, DCs)
    logging.info("All DC scans completed.")


if __name__ == "__main__":
    main()
