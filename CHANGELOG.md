# Changelog

## [3.0.2] - 2026-06-18
#132 Add timestamps to thread snapshots in All Threads section by @kkazmierczyk in #297
#298 Add support for chart zoom functionality by @kkazmierczyk in #299
#276 Implement integration with WatsonX LLM by @kkazmierczyk in #289

[3.0.2]: https://github.com/IBM/javacore-analyser/compare/3.0.1...3.0.2

## [3.0.1] - 2026-06-15
#220 Adding Machine Learning feature for classifying javacore threads by @fchiossi in #261
#265 Flask import error in batch mode when Flask not installed by @kkazmierczyk in #266
#271 Processing har fails with IndexError: list index out of range by @kkazmierczyk in #272
#269 Set root logger to DEBUG for wait2-debug.log by @kkazmierczyk in #270
#268 jQuery tablesorter initialization for plugin-generated tables by @kkazmierczyk in #267
#278 files called verbosegclog are not recognised by @PiotrAniola82 in #279
#285 ML classification fails for thread snapshot in state UNKNOWN and issue #288 classify_javacore_inference causes a circular import. by @fchiossi in #287
#280 support for tar files by @kkazmierczyk in #283
#274 HAR file special characters handling by @kkazmierczyk in #275
#290 detect system exit in main thread by @kkazmierczyk in #291

[3.0.1]: https://github.com/IBM/javacore-analyser/compare/3.0.0...3.0.1

## [3.0] - 2026-05-12

### Main changes:
* #205 Provide the option to share the tips through LLM model by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/207
* #230 Introduce optional dependencies. It allows to reduce the number of dependencies if you do not use enhanced features like AI or web interface by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/231
* #1 Add more parameters for verbose gc chart by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/241
* #248 add more data for har files by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/249
* #211: Add path validation to prevent Zip Slip vulnerability by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/212
* #105 Design plugin architecture by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/257

### Full changeset
* #1 Add more parameters for verbose gc chart by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/241
* #160 Generating learning dataset by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/163
* #172 Added Ollama-based AI capability by @PiotrAniola82 in https://github.com/IBM/javacore-analyser/pull/171
* #174 properties from file with singleton by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/176
* #191 running csv dataset generator fails because properties are not initialised by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/192
* #177 make llm model selection configurable in cmd by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/178
* #179 generate llm response using the code from huggingface by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/180
* #202: Create specific exception for invalid LLM method by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/204
* #206 console logging level to prevent DEBUG messages in output by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/208
* #205 Add AI-powered performance recommendations and improve type safety by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/207
* #223 Divide report.xsl into sections for plugin architecture by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/224
* #219 Store AI prompts in text files separately from code by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/225
* #230: implement optional dependencies for packaging by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/231
* #226 Make javacores optional in report generation by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/227
* #246 Update agents.md by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/247
* #242 Add support for default LLM options by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/243
* #248 add more data for har files by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/249
* #251 Add support for long GC pause detection by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/252
* #253 Add gc pause time to ai prompt by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/254
* #255 Enhance performance recommendations prompt  by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/256
* #105 Design plugin architecture by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/257
* #259 Upload dist fails with error 400 by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/260
* #211: Add path validation to prevent Zip Slip vulnerability by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/212

[3.0]: https://github.com/IBM/javacore-analyser/compare/2.5.0...3.0.0

## [2.5.0] - 2025-09-16
* #130 script to generate javacore collector for linux by @sonaleegupta in https://github.com/IBM/javacore-analyser/pull/146
* #167 add collector file to release assets by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/168
* #165 Add information about collectors to documentation. by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/166

[2.5.0]: https://github.com/IBM/javacore-analyser/releases/tag/2.5.0

## [2.4.2] - 2025-06-16
* #156 LookupError-unknown-encoding-available by @tjanasiewicz in https://github.com/IBM/javacore-analyser/pull/157

[2.4.2]: https://github.com/IBM/javacore-analyser/releases/tag/2.4.2

## [2.4.1] - 2025-05-20
* #142 treat any thread with a truncated stack as interesting by @PiotrAniola82 in https://github.com/IBM/javacore-analyser/pull/148

[2.4.1]: https://github.com/IBM/javacore-analyser/releases/tag/2.4.1

## [2.4.0] - 2025-04-24
* Removing vagueness by @yashrajmotwani23 in https://github.com/IBM/javacore-analyser/pull/134
* Fixed javacore drilldown does not contain thread names by @PiotrAniola82 in https://github.com/IBM/javacore-analyser/pull/136
* #24 main page style by @sonaleegupta in https://github.com/IBM/javacore-analyser/pull/138
* #129 Set absolute path for reports dir. by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/137
* #140 Add to the documention option to use volumes for containers. by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/141

[2.4.0]: https://github.com/IBM/javacore-analyser/releases/tag/2.4.0

## [2.3] - 2025-02-25
* #126 allow skipping drilldown generation for uninteresting threads by @PiotrAniola82 in https://github.com/IBM/javacore-analyser/pull/128

[2.3]: https://github.com/IBM/javacore-analyser/releases/tag/2.3

## [2.2] - 2025-02-11
* #69 use normpath for paths. by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/85
* #86 Add har file support by @PiotrAniola82 in https://github.com/IBM/javacore-analyser/pull/89
* #87 Better logging when processing is failing by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/88
* #101 - improve the message regarding generating placeholder htmls by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/102
* #99 Do not include test dir to source package for pip by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/100
* #47 Create official container image by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/84
* #61 Adopt env properties for dockerfile by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/77
* #107 Improve performance of processing verbose gc files. by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/108
* #97 Changed the way how the data are fetched (from innerHTML to innerText) and condition to add only numbers was added. by @tjanasiewicz in https://github.com/IBM/javacore-analyser/pull/113
* #111 Pass tool version to dockerfile by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/112
* #106 Add the address of the thread in the thread name by @PiotrAniola82 in https://github.com/IBM/javacore-analyser/pull/114
* #117 Add brackets to ARG in Dockerfile by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/118
* #121 Replace the wait name with javacore analyser in the code by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/122
* #123 Add startup time and command line to the report by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/124

[2.2]: https://github.com/IBM/javacore-analyser/releases/tag/2.2

## [2.1] - 2025-01-02
* Fixes #66 Move information about progress bar after information about number of threads by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/67
* #27 there is no progress indicator on the web app by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/59
* #57 Add more progress bars in the code by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/58
* Expanding stack traces that contain search result by @PiotrAniola82 in https://github.com/IBM/javacore-analyser/pull/70
* Fixes #60 Switch to use cmd properties in web app by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/72
* Fixed PEP warnings by @PiotrAniola82 in https://github.com/IBM/javacore-analyser/pull/75
* #20 generate docker image by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/48
* Create _main_ class by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/80
* Different time range on gc activity and cpu load graphs by @PiotrAniola82 in https://github.com/IBM/javacore-analyser/pull/76

[2.1]: https://github.com/IBM/javacore-analyser/releases/tag/2.1

## [2.0] - 2024-12-03
* #10 extract api methods by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/11
* #8 generate web application by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/23
* System information xmx value is blank when xmx does not have units  by @PiotrAniola82 in https://github.com/IBM/javacore-analyser/pull/36
* #18-GC-activity-chart-shows-wrong-values-when-xmx-has-no-units by @tjanasiewicz in https://github.com/IBM/javacore-analyser/pull/45
* #14 Implemented progressbars by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/15
* #12 generate pip package by @kkazmierczyk in https://github.com/IBM/javacore-analyser/pull/37
* Tidied up the expensive operation message by @PiotrAniola82 in https://github.com/IBM/javacore-analyser/pull/56
* Switched the doc link to point to the public wiki on github by @PiotrAniola82 in https://github.com/IBM/javacore-analyser/pull/54
* Added search bar to thread.xsl and javacore.xsl by @PiotrAniola82 in https://github.com/IBM/javacore-analyser/pull/51
* Updated the input/output arguments of the javacore_analyser_batch. by @tjanasiewicz in https://github.com/IBM/javacore-analyser/pull/63

[2.0]: https://github.com/IBM/javacore-analyser/releases/tag/2.0

## [1.0] - 2024-10-25

### Added
- Initial product release
  
[1.0]: https://github.com/IBM/javacore-analyser/releases/tag/v1.0
