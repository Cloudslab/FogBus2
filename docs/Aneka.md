# Aneka 5.0 Installation Guide

This is a brief installation guide
of [Aneka 5.0](http://www.manjrasoft.com/download/5.0/Aneka5.0ReleaseNotes.pdf).
This guide aims to help users gain some instant experience on Aneka. Thus,
details of some config will not be explained. However, it is highly recommended
that users should learn more
about [Aneka](http://www.manjrasoft.com/products.html) before getting deeper.

## Environment

- Windows Server (Any version with .NET 4.5 supports)

## Package

- Aneka 5.0
    + Go
      to [Manjrasoft Download Center](http://www.manjrasoft.com/manjrasoft_downloads.html)
      ,
      click [Aneka 5.0 Software (Free Evaluation Version) Direct Download](http://www.manjrasoft.com/download/5.0/Aneka5.0.msi)

## Installation

1. Run installer `Aneka5.0.msi`, click `Next`.
2. Set your installation folder and account, click `Next`.
3. Click `Next` to confirm installation and wait for the processing. This may
   take minutes. If the processing is stuck, unfortunately, please cancel this
   installation, go back to step 2, and install for every one of the systems.
4. You will see Aneka 5.0 has been successfully installed. Now `Close`.

## Configuration

### Aneka Node

With Aneka 5.0 installed, you will find the `Aneka Management Studio` in `Start`
-> `Recently Added`. If there is not, navigate to your installing folder, you
can find `Aneka Management Studio` should be located
under `Tools\Management Studio\`.

1. Run `Aneka Management Studio`,
2. Provide your config file if any, otherwise click `No`.
3. Set up your repository. Click `No` to use the local repository. You can also
   use a remote repository. A tool named `Aneka Default FTP` can be used to run
   an `FTP Service` at the same folder of `Aneka Management Studio`.
4. Then set this machine to be an Ankea node. Click `File` in the menu
   and `Add Machine`.
5. Set `Host or IP` to be your machine's accessible IP. Don't forget to open the
   port both firewall on the system and on the control panel of your provider.
6. Drop down `Credentials`, create a credential and use it. This credential
   should be the account name and password of the machine you are using. After
   preparing all this information, click `OK`.
7. In the left sidebar, click `Uninstalled Allocated`. You will see a red cross
   which indicated with the IP or Host you provided in the last step.
   Right-click on it, then click `install`.
8. Set listening port and repository address. Click `Next` and `Finish`. You
   will then find the machine in `Installed Allocated`.

### Aneka Containers

#### Master

1. Right-click on the node, then click `Install Container`, fill accessible IP.
2. Select 'Master', click `Next` and 'Next'.
3. You need to configure persistence now. If you need the data as like how much
   resources a task uses, you need to select `Relational Database`, otherwise
   select `In Memory`.
4. After the database is configured, click `Next`. Configure container
   properties according to your machine's cost, then click `Next` and 'Next'.
5. In `Advanced Services Configuration` panel, double click to check every
   service on the list. Then click `Next` and `Finish`. You will find the master
   container under `Containers > Master Containers`.

#### Worker

1. Go to `Installed Allocated`, right-click on your Aneka node,
   click `Install Container`.
2. Set the accessible IP.
3. Dropdown and select `Worker`, make sure Master Container address is correct.
   Use `Probe` to check the availability.
4. Set an available port for the worker. And then click `Next`, `Next`
   and `Next`.
5. Configure container properties according to your machine's cost, then
   click `Next`, `Next`, `Next` and `Finish`.
6. In the left sidebar, click `Containers`, you will find all containers you
   have here.

## Test Aneka Cloud

1. Under the same folder of `Aneka Management Studio`, find `Mandelbrot` and
   run.
2. Click play button.
3. Set master address. If the container can be accessed locally, the credential
   is no necessary. Otherwise, provide a credential to access the container.
4. Click `Ok` to compute. You will see the processing in progress.

Congratulations! You have an Aneka Cloud running now! The next step will be
developing applications using Aneka to compute. Documentations and example codes
are always available for a
developer [here](http://www.manjrasoft.com/manjrasoft_downloads.html#Aneka%20User%20Documents)
.
