#
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: Apache-2.0
#

import os
import unittest

from javacore_analyser.javacore import Javacore
from javacore_analyser.javacore_set import JavacoreSet
from javacore_analyser.thread_snapshot import ThreadSnapshot


class TestJavacore(unittest.TestCase):

    def setUp(self):
        self.javacore_set = JavacoreSet('data' + os.path.sep + 'javacores')
        self.filename = 'test' + os.path.sep + 'data' + os.path.sep + 'javacores' + os.path.sep + 'javacore.20220606.114458.32888.0001.txt'
        self.javacore = Javacore()
        self.javacore.create(self.filename, self.javacore_set)

    def test_get_encoding(self):
        encoding = self.javacore.get_encoding()
        self.assertEqual(encoding, '1252')

    def test_parse_snapshot_data(self):
        self.assertEqual(201, len(self.javacore.snapshots))

    def test_extract_thread_snapshots(self):
        self.javacore.extract_thread_snapshots()
        name = "[SQL@10:46:40.849], select  distinct t2.APPROVER_ITEM_ID, t3.USER_ID, t3.NAME from \n\
(select t1q.*, T1V.ITEM_TYPE_DBID from QM1USER.DEPLOYMENT_QUALITY_APPROVAL t1q\n\
 inner join QM1USER.REPOSITORY_VERSION T1V on T1V.STATE_ID = t1q.STATE_ID\n\
 where T1V.ITEM_TYPE_DBID = ? and T1V.CONFIG_ID = ? and T1V.IS_CURRENT = 1\n\
)\n\
 t1 inner join QM1USER.DEPLMNT_QLT_PPRVL_NTRNL_PPRVLS t2 on (t1.INTERNAL_APPROVALS = t2.JZ_PARENT_ID) left outer join QM1USER.REPOSITORY_CONTRIBUTOR t3 on (t2.APPROVER_ITEM_ID = t3.ITEM_ID); WebContainer : 2 @@ 10:46 test User Agent@127.0.0.1> /qm/service/com.ibm.rqm.integration.service.IIntegrationService/resources/_k2qXBD9NEeuAse2ddn7Yjw/testcase"

        for snapshot in self.javacore.snapshots:
            if snapshot.thread_id == '0xFE':
                normalised_name = snapshot.name.replace("\r\n", "\n")
                assert(normalised_name == name)
                return
        self.fail('multiline thread name not found')
        pass

    def test_parse_siginfo(self):
        t = self.javacore.siginfo
        self.assertEqual(t, 'Dump Requested By User (00100000) Through com.ibm.jvm.Dump.javaDumpToFile')

    def test_parse_javacore_date_time(self):
        t = self.javacore.parse_javacore_date_time()
        self.assertEqual(t.strftime('%Y-%m-%d %H:%M:%S.%f'), '2022-06-06 11:44:58.407000')

    def test_get_snapshot_by_name(self):
        snapshot_name = self.javacore.get_snapshot_by_name('kernel-command-listener').name
        snapshot_name_from_test_javacore = self.javacore.snapshots[0].name
        self.assertEqual(snapshot_name, snapshot_name_from_test_javacore)

    def test_basefilename(self):
        self.assertEqual(self.javacore.basefilename(), 'javacore.20220606.114458.32888.0001.txt')

    def test_get_cpu_percentage_and_load(self):
        jset = JavacoreSet("")
        jset.number_of_cpus = 2
        javacore = Javacore()
        javacore.javacore_set = jset
        self.assertEqual(javacore.get_cpu_percentage(),0)
        self.assertEqual(javacore.get_load(), 0)
        javacore = Javacore()
        javacore.javacore_set = jset
        s1 = ThreadSnapshot()
        s1.cpu_usage_inc = 10
        s1.elapsed_time = 100
        javacore.snapshots.append(s1)
        self.assertEqual(javacore.get_cpu_percentage(), 5)
        self.assertEqual(javacore.get_load(), 0.1)
        javacore = Javacore()
        javacore.javacore_set = jset
        s2 = ThreadSnapshot()
        s2.cpu_usage_inc = 5
        s2.elapsed_time = 100
        javacore.snapshots.append(s1)
        javacore.snapshots.append(s2)
        self.assertEqual(javacore.get_cpu_percentage(), 7.5)
        self.assertEqual(javacore.get_load(), 0.15)
