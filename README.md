<!-- This should be the location of the title of the repository, normally the short name -->
# Javacore Analyser

![GitHub License](https://img.shields.io/github/license/IBM/javacore-analyser)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/javacore-analyser)
![GitHub contributors](https://img.shields.io/github/contributors/IBM/javacore-analyser)  
<!-- Build Status, is a great thing to have at the top of your repository, it shows that you take your CI/CD as first class citizens -->
[![Build Status](https://app.travis-ci.com/IBM/javacore-analyser.svg?token=w3i4X11XppEi2tJQsxDb&branch=main)](https://app.travis-ci.com/IBM/javacore-analyser)
![GitHub last commit](https://img.shields.io/github/last-commit/IBM/javacore-analyser)
![GitHub Release Date](https://img.shields.io/github/release-date/IBM/javacore-analyser)
![GitHub commit activity](https://img.shields.io/github/commit-activity/t/IBM/javacore-analyser)
![GitHub Issues or Pull Requests](https://img.shields.io/github/issues-pr/IBM/javacore-analyser)
![GitHub Issues or Pull Requests](https://img.shields.io/github/issues-pr-closed/IBM/javacore-analyser)
![PyPI - Downloads](https://img.shields.io/pypi/dm/javacore-analyser)


<!-- Not always needed, but a scope helps the user understand in a short sentance like below, why this repo exists -->
## Scope

The tool analyzes Javacores and verbose gc logs and provides some reports like cpu/gc usage, blocked threads, some tips regarding the javacores. The tool can process the following data:
* Set of Javacores from the same run. Optionally you can add verbose.gc log file
* Single Javacore

  
<!-- A more detailed Usage or detailed explaination of the repository here -->
## Installation and usage

### Installation:
The tool requires Python 3.9 or higher plus some packages - see more in [REQUIREMENTS](REQUIREMENTS.md). 
Despite it is not mandatory, it is recommended in Python to use virtual environment to manage packages.

#### Installing from pip
This is most common option which you will need in 99% of situations  

Steps:
1. Download and install Python. Usually the latest version is supported. Search for supported versions in 
[REQUIREMENTS](REQUIREMENTS.md)
2. Create and activate Virtual Environment according to [Creating virtual environments](https://docs.python.org/3/tutorial/venv.html#creating-virtual-environments).
3. Run the following command:
   `pip install javacore-analyser`  
    OR
   `pip install --pre javacore-analyser` - if you want an experimental version


#### Installing from sources
This is recommended for geeks only:
1. Repeat steps 1 and 2 from above
2. Download the project files either from [Releases](https://github.com/IBM/javacore-analyser/releases) or from [main](https://github.com/IBM/javacore-analyser/archive/refs/heads/main.zip)
3. Extract the code and from code directory execute
   `pip install .`

### Running the tool:

#### Running cmd application: 
1. Install application if not done yet
2. Activate your created virtual environment according to activate Virtual Environment according to [Creating virtual environments](https://docs.python.org/3/tutorial/venv.html#creating-virtual-environments)
3. Run the following command from cmd:  
`javacore-analyser-batch <input-data> <generated-reports-dir>`  
or  
`python -m javacore_analyser batch <input-data> <generated-reports-dir>`  

Where `<input-data>` is one of the following:
* The directory containing javacores and optionally verbose gc
* Archive (7z, zip, tar.gz, tar.bz2) containing the same
* List of the javacores separated by `;` character. Optionally you can add `--separator` option to define your own separator.
You can type the following command to obtain the help:  
`javacore-analyser-batch --help` or `python -m javacore_analyser batch --help`

#### Running web application:
1. Repeat steps 1-3 from cmd application
2. Execute the following command from cmd:  
  `javacore_analyser_web --port=5000 --reports-dir=/data/reports_dir`  
     or  
  `python -m javacore_analyser web --port=5000 --reports-dir=/data/reports_dir`  

   The first parameter set the port to use by application. If not specified, 5000 will be used.  
   The second parameter sets where the reports need to be stored. If not set, then the `reports` dir will be created in current location.  

Now you can type (http://localhost:5000/).  

### Running container image
There is an unofficial Docker/Podman container managed by one of projects developers. Use the following command 
to start it:

`podman run -it --rm --name javacore-analyser --mount type=bind,src="/local-reports-dir",target=/reports -p 5001:5000 ghcr.io/kkazmierczyk/javacore-analyser:latest`

or  
`docker run -it --rm --name javacore-analyser --mount type=bind,src="/local-reports-dir",target=/reports -p 5001:5000 ghcr.io/kkazmierczyk/javacore-analyser:latest`  

The `mount` option specifies where you want locally to store the reports. The reports in the container are stored in 
`/reports` directory. If you remove mount option, the application will work but the reports will not persist after 
restart.  
The application is running in the container on port 5000. By using `-p 5001:5000` option, you specify to map container 
port 5000 to port 5001 on your machine. Therefore the application will be available under `http://localhost:5001/`.
 
<!-- The following are OPTIONAL, but strongly suggested to have in your repository. -->
<!--
* [dco.yml](.github/dco.yml) - This enables DCO bot for you, please take a look https://github.com/probot/dco for more details.
* [travis.yml](.travis.yml) - This is a example `.travis.yml`, please take a look https://docs.travis-ci.com/user/tutorial/ for more details.
-->

<!-- A notes section is useful for anything that isn't covered in the Usage or Scope. Like what we have below. -->
## Notes

<!--
**NOTE: This repository has been configured with the [DCO bot](https://github.com/probot/dco).
When you set up a new repository that uses the Apache license, you should
use the DCO to manage contributions. The DCO bot will help enforce that.
Please contact one of the IBM GH Org stewards.**
-->


<!-- Questions can be useful but optional, this gives you a place to say, "This is how to contact this project maintainers or create PRs -->
If you have any questions or issues you can create a new [issue here][issues].

Pull requests are very welcome! Make sure your patches are well tested.
Ideally create a topic branch for every separate change you make. For
example:

1. Fork the repo
2. Create your feature branch (`git checkout -b my-new-feature`)
3. Commit your changes (`git commit -am 'Added some feature'`)
4. Push to the branch (`git push origin my-new-feature`)
5. Create new Pull Request

## License

All source files must include a Copyright and License header. The SPDX license header is 
preferred because it can be easily scanned.

If you would like to see the detailed LICENSE click [here](LICENSE).

```text
#
# Copyright IBM Corp. {Year project was created} - {Current Year}
# SPDX-License-Identifier: Apache-2.0
#
```
## Authors

* Krzysztof Kazmierczyk <kazm@ibm.com>
* Piotr Aniola <Piotr.Aniola@ibm.com>
* Tadeusz Janasiewicz <t.janasiewicz@ibm.com>

[issues]: https://github.com/IBM/javacore-analyser/issues/new

## Another pages

Another useful pages:
* [LICENSE](LICENSE)
* [README.md](README.md)
* [CONTRIBUTING.md](CONTRIBUTING.md)
* [MAINTAINERS.md](MAINTAINERS.md)
<!-- A Changelog allows you to track major changes and things that happen, https://github.com/github-changelog-generator/github-changelog-generator can help automate the process -->
* [CHANGELOG.md](CHANGELOG.md)
* [REQUIREMENTS.md](REQUIREMENTS.md)
