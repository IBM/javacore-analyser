<!-- This should be the location of the title of the repository, normally the short name -->
# Javacore Analyser

<!-- Build Status, is a great thing to have at the top of your repository, it shows that you take your CI/CD as first class citizens -->
[![Build Status](https://app.travis-ci.com/IBM/javacore-analyser.svg?token=w3i4X11XppEi2tJQsxDb&branch=main)](https://app.travis-ci.com/IBM/javacore-analyser)

<!-- Not always needed, but a scope helps the user understand in a short sentance like below, why this repo exists -->
## Scope

The tool analyzes Javacores and verbose gc logs and provides some reports like cpu/gc usage, blocked threads, some tips regarding the javacores. The tool can process the following data:
* Set of Javacores from the same run. Optionally you can add verbose.gc log file
* Single Javacore

  
<!-- A more detailed Usage or detailed explaination of the repository here -->
## Installation and usage

### Installation:
The tool requires Python 3.9 or higher plus some packages - see more in [REQUIREMENTS](REQUIREMENTS.md). Despite it is not mandatory, it is recommended in Python to use virtual environment to manage packages.

Steps:
1. Download and install Python. Usually the latest version is supported. Search for supported versions in 
[REQUIREMENTS](REQUIREMENTS.md)
2. Download and unpack the tool.
3. Create and activate Virtual Environment according to [Creating virtual environments](https://docs.python.org/3/tutorial/venv.html#creating-virtual-environments).
4. Install all required pip packages. Navigate in command line to unpacked tool and type
   `pip install -r requirements.txt`

### Running the tool:
1. Activate your created virtual environment according to activate Virtual Environment according to [Creating virtual environments](https://docs.python.org/3/tutorial/venv.html#creating-virtual-environments)
2. Navigate in command line to unpacked tool and run the following command:  
  `python javacore_analyzer.py <input-data> <output-dir>`  
Where `<input-data>` is one of the following:
* The directory containing javacores and optionally verbose gc
* Archive (7z, zip, tar.gz, tar.bz2) containint the same
* List of the javacores separated by `'` character. Optionally you can add `--separator` option to define your own separator.
You can type the following command to obtain the help:  
`python javacore_analyzer.py --help`


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
