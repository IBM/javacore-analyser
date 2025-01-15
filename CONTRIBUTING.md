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
2. Add the following parameters:  
   **debug=True reports_dir=/tmp/web_reports**  

   You can change the report dir to the location when you want to store the report. 
   The application will start on http://localhost:5000


## Build pip package 
Follow the steps from [Packaging projects](https://packaging.python.org/en/latest/tutorials/packaging-projects/).
Currently Chris has an API keys for test and production pypi

## Build container localy  
To build a container:  
`podman build -t javacore-analyser .`

or 

`docker build -t javacore-analyser .`

To start the container:  
`podman run -it --rm --name javacore-analyser --mount type=bind,src="local-dir-on-fs",target=/reports -p 5001:5000 javacore-analyser`  

or

`docker run -it --rm --name javacore-analyser --mount type=bind,src="local-dir-on-fs",target=/reports -p 5001:5000 javacore-analyser`

`src` parameter specifies where you want to store reports locally  
`-p` specifies port mapping. The application in container is running on port 5000. You can map it to another port on 
your machine (5001 in this example).

## Releasing a new version
Release a new version is partially automated by Travis. Here are the steps:  
1. Make sure you are on `main` branch in your repository.
2. Create a new tag e.g:  
   `git tag 2.1`
3. Push the tag to Github:  
  `git push --tags`  
  alternatively you can perform this operation from Pycharm UI (**Git** -> **Push** -> Select **Push Tags** -> 
  Click **Push**)  
   
   Creating a new tag invokes a build operation which is doing the following:
   * The following code 
      ```yaml
     deploy:
      - provider: script
        #script: python -m twine upload --skip-existing --verbose --password $TWINE_TEST_TOKEN --repository testpypi dist/* #test instance
        script: python -m twine upload --skip-existing --verbose --password $TWINE_PROD_TOKEN dist/* #production instance.  
        on:  
        # all_branches: true # uncomment for testing purposes
          branch: prod # uncomment on production
          tags: true # We need to consider if we want to publish all versions or every build (which should not be an issue
     ```
     Is publishing pip package to pip repository. You are setting all passwords here: 
     https://app.travis-ci.com/github/IBM/javacore-analyser/settings section **Environmental Variables**.
     **TWINE_USERNAME** should be set to **__token__** and **TWINE_PROD_TOKEN** or **TWINE_TEST_TOKEN** are the tokens
     set on pipy page (https://pypi.org/manage/account/token/ or https://test.pypi.org/manage/account/token/).
   * The following code:
     ```yaml
      - provider: releases
        edge: true
        draft: true
        file: dist/*
        on:
          # all_branches: true # uncomment for testing purposes
          branch: prod # uncomment on production
          tags: true # We need to consider if we want to publish all versions or every build (which should not be an issue
     ```  
     Generates the new **Draft** release on Github and adds distribution files (They are located in `dist/*`).
     This code requires setting **GITHUB_TOKEN** variable in 
     https://app.travis-ci.com/github/IBM/javacore-analyser/settings. You can generate github token on 
https://github.com/settings/tokens/new
4. Navigate in Github to the new Draft release page. You can easily find it on 
   https://github.com/IBM/javacore-analyser/releases
5. Click on Edit pen and then click on **Generate release notes** and edit them before saving.
6. Publish release.
7. Copy release notes to [CHANGELOG.md](CHANGELOG.md) file.

## Testing
As default the tests in Pycharm are ran in the current selected directory. However we want to run them in main 
directory of the tool (**javacore-analyser** directory, not **test** directory). 
1. Right click on **test** directory in **Project** view and select **Modify Run Configuration...**. 
When the window appears, the **Working Directory** will be set to **test** directory. 
Change it to **javacore-analyser** directory
2. Right click again on **test** and select **Run** or **Debug**.

## Coding style guidelines
We use [PEP 8](https://peps.python.org/pep-0008/) Python style for Python files.
