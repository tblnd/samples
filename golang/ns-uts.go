package main

import (
	"fmt"
	"os"
	"os/exec"
	"syscall"
)

func main() {
	exec.Command("/bin/bash")
	cmd := exec.Cmd{
		Path:   "/bin/bash",
		Stdin:  os.Stdin,
		Stdout: os.Stdout,
		Stderr: os.Stderr,
		SysProcAttr: &syscall.SysProcAttr{
			Cloneflags: syscall.CLONE_NEWUTS,
		},
	}
	if err := cmd.Run(); err != nil {
		fmt.Println(err)
	}
}
