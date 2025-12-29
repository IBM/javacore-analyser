#
# Copyright IBM Corp. 2024 - 2025
# SPDX-License-Identifier: Apache-2.0
#

CPU_NUMBER_TAG = "3XHNUMCPUS"
CPU_TIME = "3XMCPUTIME"
THREAD_INFO = "3XMTHREADINFO"
ALLOCATED_MEM = "3XMHEAPALLOC"
USER_ARGS = "2CIUSERARG"
XMX = "Xmx"
XMS = "Xms"
XMN = "Xmn"
GC_POLICY = "Xgcpolicy"
COMPRESSED_REFS = "Xcompressedrefs"
NO_COMPRESSED_REFS = "Xnocompressedrefs"
VERBOSE_GC = "verbose:gc"
OS_LEVEL = "2XHOSLEVEL"
ARCHITECTURE = "3XHCPUARCH"
JAVA_VERSION = "1CIJAVAVERSION"
THREAD_ID = '3XMJAVALTHREAD'
THREAD_BLOCK = '3XMTHREADBLOCK'
UNKNOWN = 'Unknown'
STACK_TRACE = '4XESTACKTRACE'
NATIVE_STACK_TRACE = '4XENATIVESTACK'
DATETIME = '1TIDATETIME'
STARTTIME = '1CISTARTTIME'
SIGINFO = '1TISIGINFO'
ENCODING = '1TICHARSET'
CMD_LINE = '1CICMDLINE'

DATA_OUTPUT_SUBDIR = '/data/'

MIN_JAVACORE_SIZE = 5 * 1024  # Minimal Javacore size in bytes

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Web application constants
TEMP_DIR = "temp_data"  # Folder to store temporary data for creating reports

# Used for extracting hugging face llm
ASSISTANT_ROLE = '<|start_of_role|>assistant<|end_of_role|>'
END_OF_TEXT = '<|end_of_text|>'
