
#! /bin/sh

set -e

sudo wg set wg0 peer NFFC0V+ZH/Q9FqV9/1ELfmZKluybv/0TaVBRijKaMXo= allowed-ips 10.0.0.1/32 endpoint 192.168.3.20:4500  persistent-keepalive 5

sudo wg set wg0 peer fAPjjeBrqAIAjKely/2bYY/THgT3nc0G5xlem42dPUY= allowed-ips 10.0.0.101/32 endpoint 192.168.3.49:4501  persistent-keepalive 5

sudo wg set wg0 peer PEcydD2LL48GHmHuH4eN6yU/W3kDFU+UTdB5VjTstE8= allowed-ips 10.0.0.102/32 endpoint 192.168.3.73:4502 persistent-keepalive 5

sudo wg set wg0 peer /ia/qcvq+LIP3AjjUv1Deeb+4JslXBOStVs3WDL2nRw= allowed-ips 10.0.0.103/32 endpoint 192.168.3.14:4503 persistent-keepalive 5

sudo wg set wg0 peer RlUr3SOmzYsAt/15BwVyC7J1PCqO6BKKWweC5penMUk= allowed-ips 10.0.0.104/32 endpoint 192.168.3.72:4504 persistent-keepalive 5

sudo wg set wg0 peer 30MJfFVxvK+qwTZIO9Eqx6/ebwe1gA1FGgMU59r5SR0= allowed-ips 10.0.0.201/32 endpoint 124.70.186.56:4500 persistent-keepalive 5

sudo wg set wg0 peer HsyvFnmirkqMcaZ8HSA9cu+3f/pvMyf9jtnfEUlr4TU= allowed-ips 10.0.0.202/32 endpoint 124.71.175.60:4600 persistent-keepalive 5

sudo wg set wg0 peer et9IMxRjanM/NepFxkj0IT/nz29EeYR+xdNvkwvu/EI= allowed-ips 10.0.0.203/32 endpoint 121.36.208.140:4500 persistent-keepalive 5

sudo wg set wg0 peer gFAqXUzvGyR746gj1aJpguTHOyp850NOKExIKk8EyTc= allowed-ips 10.0.0.204/32 endpoint 123.60.23.104:4500 persistent-keepalive 5

sudo wg set wg0 peer o+O4WpGGW+LICx3r1FU9r26ZjKW58vuhDMzmEDpjGDU= allowed-ips 10.0.0.205/32 endpoint 121.36.249.0:4500 persistent-keepalive 5