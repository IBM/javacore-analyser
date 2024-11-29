## Contributing In General
Our project welcomes external contributions. If you have an itch, please feel
free to scratch it.

To contribute code or documentation, please submit a [pull request](https://github.com/IBM/javacore-analyser/compare).

A good way to familiarize yourself with the codebase and contribution process is
to look for and tackle low-hanging fruit in the [issue tracker](https://github.com/ibm/javacore-analyser/issues).
Before embarking on a more ambitious contribution, please quickly [get in touch](#communication) with us.

**Note: We appreciate your effort, and want to avoid a situation where a contribution
requires extensive rework (by you or by us), sits in backlog for a long time, or
cannot be accepted at all!**

### Proposing new features

If you would like to implement a new feature, please 
[raise an issue](https://github.com/IBM/javacore-analyser/issues/new)
before sending a pull request so the feature can be discussed. This is to avoid
you wasting your valuable time working on a feature that the project developers
are not interested in accepting into the code base.

### Fixing bugs

If you would like to fix a bug, please [raise an issue](https://github.com/IBM/javacore-analyser/issues/new) before 
sending a pull request so it can be tracked.

### Merge approval

The project maintainers use LGTM (Looks Good To Me) in comments on the code
review to indicate acceptance. A change requires LGTMs from two of the
maintainers of each component affected.

For a list of the maintainers, see the [MAINTAINERS.md](MAINTAINERS.md) page.

## Legal

Each source file must include a license header for the Apache
Software License 2.0. Using the SPDX format is the simplest approach.
e.g.

```
/*
Copyright <holder> All Rights Reserved.

SPDX-License-Identifier: Apache-2.0
*/
```

We have tried to make it as easy as possible to make contributions. This
applies to how we handle the legal aspects of contribution. We use the
same approach - the [Developer's Certificate of Origin 1.1 (DCO)](https://github.com/hyperledger/fabric/blob/master/docs/source/DCO1.1.txt) - that the Linux® Kernel [community](https://elinux.org/Developer_Certificate_Of_Origin)
uses to manage code contributions.

We simply ask that when submitting a patch for review, the developer
must include a sign-off statement in the commit message.

Here is an example Signed-off-by line, which indicates that the
submitter accepts the DCO:

```
Signed-off-by: John Doe <john.doe@example.com>
```

You can include this automatically when you commit a change to your
local git repository using the following command:

```
git commit -s
```

## Communication
Please feel free to connect with us on our [Slack channel](https://ibm.enterprise.slack.com/archives/C01KQ4X0ZK6).

## Setup
1. Install Pycharm
2. Navigate to **Project from Version Control...** and follow next steps

To run the tool with sample data perform the following steps:
1. Right click on **javacore_analyzer.py** directory in **Project** view and select **Modify Run Configuration...**. 
When the window appears, add the following commandline to **run parameters**  
`test/data/javacores /tmp/javacoreanalyser_output`  
Change the second parameter to the directory where you want the output report be created.
2. Right click again on **javacore_analyser.py** and select **Run** or **Debug**.

To run web application:
1. Right click on **javacore_analyser_web.py** directory in **Project** view and select **Modify Run Configuration...**.
2. Add the following **Environmental variables:**
   * **DEBUG:True**
   * **REPORTS_DIR:/tmp/web_reports**  
   You can change the report dir to the location when you want to store the report. 
   The application will start on http://localhost:5000


## Build pip package 
Follow the steps from [Packaging projects](https://packaging.python.org/en/latest/tutorials/packaging-projects/).
Currently Chris has an API keys for test and production pypi

## Testing
As default the tests in Pycharm are ran in the current selected directory. However we want to run them in main 
directory of the tool (**javacore-analyser** directory, not **test** directory). 
1. Right click on **test** directory in **Project** view and select **Modify Run Configuration...**. 
When the window appears, the **Working Directory** will be set to **test** directory. 
Change it to **javacore-analyser** directory
2. Right click again on **test** and select **Run** or **Debug**.

## Coding style guidelines
We use [PEP 8](https://peps.python.org/pep-0008/) Python style for Python files.
