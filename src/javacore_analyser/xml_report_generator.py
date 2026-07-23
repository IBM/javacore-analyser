#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#

import logging
from datetime import datetime
from xml.dom.minidom import parseString

from javacore_analyser.constants import DATE_FORMAT


class XmlReportGenerator:
    """Generates the XML report file from a JavacoreAnalyzer (or JavacoreSet) instance."""

    @staticmethod
    def create_report_xml(javacore_analyzer, output_file):
        """Generate an XML report containing information about the javacore data.

        Args:
            javacore_analyzer: A JavacoreAnalyzer (or JavacoreSet) instance to read data from.
            output_file (str): The path where the output XML file will be written.
        """
        logging.info("Generating report xml")

        doc = parseString('''<?xml version="1.0" encoding="UTF-8" ?>
        <?xml-stylesheet type="text/xsl" href="data/report.xsl"?><doc/>''')

        doc_node = doc.documentElement

        # Add data types information
        data_types_node = doc.createElement("data_types")
        doc_node.appendChild(data_types_node)
        for data_type in javacore_analyzer.data_types:
            type_node = doc.createElement("type")
            type_node.appendChild(doc.createTextNode(data_type))
            data_types_node.appendChild(type_node)

        javacore_count_node = doc.createElement("javacore_count")
        javacore_count_node.appendChild(doc.createTextNode(str(len(javacore_analyzer.javacores))))
        doc_node.appendChild(javacore_count_node)
        report_info_node = doc.createElement("report_info")
        doc_node.appendChild(report_info_node)
        generation_time_node = doc.createElement("generation_time")
        report_info_node.appendChild(generation_time_node)
        generation_time_node.appendChild(doc.createTextNode(str(datetime.now().strftime(DATE_FORMAT))))
        doc_node.setAttribute("use_ml", str(javacore_analyzer.use_ml))

        # Only include javacore-specific data if javacores are present
        if 'javacores' in javacore_analyzer.data_types and len(javacore_analyzer.javacores) > 0:
            generation_javacores_node = doc.createElement("javacores_generation_time")
            report_info_node.appendChild(generation_javacores_node)
            generation_javacores_node_starting_time = doc.createElement("starting_time")
            generation_javacores_node.appendChild(generation_javacores_node_starting_time)
            generation_javacores_node_starting_time.appendChild(
                doc.createTextNode(str(javacore_analyzer.javacores[0].datetime.strftime(DATE_FORMAT))))
            generation_javacores_node_end_time = doc.createElement("end_time")
            generation_javacores_node.appendChild(generation_javacores_node_end_time)
            generation_javacores_node_end_time.appendChild(
                doc.createTextNode(str(javacore_analyzer.javacores[-1].datetime.strftime(DATE_FORMAT))))

            javacore_list_node = doc.createElement("javacore_list")
            report_info_node.appendChild(javacore_list_node)
            for jc in javacore_analyzer.javacores:
                javacore_node = doc.createElement("javacore")
                javacore_list_node.appendChild(javacore_node)
                javacore_file_node = doc.createElement("javacore_file_name")
                javacore_node.appendChild(javacore_file_node)
                javacore_file_node.appendChild(doc.createTextNode(jc.basefilename()))
                javacore_file_time_stamp_node = doc.createElement("javacore_file_time_stamp")
                javacore_node.appendChild(javacore_file_time_stamp_node)
                javacore_file_time_stamp_node.appendChild(
                    doc.createTextNode(str(jc.datetime.strftime(DATE_FORMAT))))
                javacore_total_cpu_node = doc.createElement("javacore_cpu_percentage")
                javacore_node.appendChild(javacore_total_cpu_node)
                javacore_total_cpu_node.appendChild(doc.createTextNode(str(jc.get_cpu_percentage())))
                javacore_load_node = doc.createElement("javacore_load")
                javacore_node.appendChild(javacore_load_node)
                javacore_load_node.appendChild(doc.createTextNode(str(jc.get_load())))
                # When ML classification is enabled, count how many thread snapshots in
                # this javacore received each classification label.
                if javacore_analyzer.use_ml:
                    classification_counts = {}
                    for snapshot in jc.snapshots:
                        label = snapshot.get_classification()
                        if label:
                            classification_counts[label] = classification_counts.get(label, 0) + 1
                    jc_classifications_node = doc.createElement("javacore_classifications")
                    javacore_node.appendChild(jc_classifications_node)
                    for label, count in classification_counts.items():
                        entry_node = doc.createElement("classification_entry")
                        entry_node.setAttribute("value", label)
                        entry_node.setAttribute("count", str(count))
                        jc_classifications_node.appendChild(entry_node)

        verbose_gc_list_node = doc.createElement("verbose_gc_list")
        report_info_node.appendChild(verbose_gc_list_node)

        total_collects_in_time_limits = 0
        for vgc in javacore_analyzer.gc_parser.get_files():
            verbose_gc_node = doc.createElement("verbose_gc")
            verbose_gc_list_node.appendChild(verbose_gc_node)
            verbose_gc_file_name_node = doc.createElement("verbose_gc_file_name")
            verbose_gc_node.appendChild(verbose_gc_file_name_node)
            verbose_gc_file_name_node.appendChild(doc.createTextNode(vgc.get_file_name()))
            verbose_gc_collects_node = doc.createElement("verbose_gc_collects")
            verbose_gc_node.appendChild(verbose_gc_collects_node)
            verbose_gc_collects_node.appendChild(doc.createTextNode(str(vgc.get_number_of_collects())))
            total_collects_in_time_limits += vgc.get_number_of_collects()
            verbose_gc_total_collects_node = doc.createElement("verbose_gc_total_collects")
            verbose_gc_node.appendChild(verbose_gc_total_collects_node)
            verbose_gc_total_collects_node.appendChild(
                doc.createTextNode(str(vgc.get_total_number_of_collects())))
        verbose_gc_list_node.setAttribute("total_collects_in_time_limits", str(total_collects_in_time_limits))

        if len(javacore_analyzer.har_files) > 0:
            har_files_node = doc.createElement("har_files")
            doc_node.appendChild(har_files_node)
            for har in javacore_analyzer.har_files:
                har_files_node.appendChild(har.get_xml(doc))

        # Only include system info if javacores are present
        if 'javacores' in javacore_analyzer.data_types:
            system_info_node = doc.createElement("system_info")
            doc_node.appendChild(system_info_node)
        else:
            system_info_node = None

        tips_node = doc.createElement("tips")
        report_info_node.appendChild(tips_node)
        for tip in javacore_analyzer.tips:
            tip_node = doc.createElement("tip")
            tips_node.appendChild(tip_node)
            tip_node.appendChild(doc.createTextNode(tip))
        tips_node.setAttribute("ai_tips", javacore_analyzer.ai_tips)

        # Only add system info details if javacores are present
        if system_info_node is not None:
            user_args_list_node = doc.createElement("user_args_list")
            system_info_node.appendChild(user_args_list_node)
            for arg in javacore_analyzer.user_args:
                arg_node = doc.createElement("user_arg")
                user_args_list_node.appendChild(arg_node)
                arg_node.appendChild(doc.createTextNode(arg))

            number_of_cpus_node = doc.createElement("number_of_cpus")
            system_info_node.appendChild(number_of_cpus_node)
            number_of_cpus_node.appendChild(
                doc.createTextNode(javacore_analyzer.number_of_cpus if javacore_analyzer.number_of_cpus else ""))

            xmx_node = doc.createElement("xmx")
            system_info_node.appendChild(xmx_node)
            xmx_node.appendChild(doc.createTextNode(javacore_analyzer.xmx))

            xms_node = doc.createElement("xms")
            system_info_node.appendChild(xms_node)
            xms_node.appendChild(doc.createTextNode(javacore_analyzer.xms))

            xmn_node = doc.createElement("xmn")
            system_info_node.appendChild(xmn_node)
            xmn_node.appendChild(doc.createTextNode(javacore_analyzer.xmn))

            verbose_gc_node = doc.createElement("verbose_gc")
            system_info_node.appendChild(verbose_gc_node)
            verbose_gc_node.appendChild(doc.createTextNode(str(javacore_analyzer.verbose_gc)))

            gc_policy_node = doc.createElement("gc_policy")
            system_info_node.appendChild(gc_policy_node)
            gc_policy_node.appendChild(doc.createTextNode(javacore_analyzer.gc_policy))

            compressed_refs_node = doc.createElement("compressed_refs")
            system_info_node.appendChild(compressed_refs_node)
            compressed_refs_node.appendChild(doc.createTextNode(str(javacore_analyzer.compressed_refs)))

            architecture_node = doc.createElement("architecture")
            system_info_node.appendChild(architecture_node)
            architecture_node.appendChild(doc.createTextNode(javacore_analyzer.architecture))

            java_version_node = doc.createElement("java_version")
            system_info_node.appendChild(java_version_node)
            java_version_node.appendChild(doc.createTextNode(javacore_analyzer.java_version))

            os_level_node = doc.createElement("os_level")
            system_info_node.appendChild(os_level_node)
            os_level_node.appendChild(doc.createTextNode(javacore_analyzer.os_level))

            jvm_startup_time = doc.createElement("jvm_start_time")
            system_info_node.appendChild(jvm_startup_time)
            jvm_startup_time.appendChild(doc.createTextNode(javacore_analyzer.jvm_start_time))

            cmd_line = doc.createElement("cmd_line")
            system_info_node.appendChild(cmd_line)
            cmd_line.appendChild(doc.createTextNode(javacore_analyzer.cmd_line))

        # Only add javacore-dependent data if javacores are present
        if 'javacores' in javacore_analyzer.data_types:
            doc_node.appendChild(XmlReportGenerator.get_blockers_xml(javacore_analyzer, doc))
            doc_node.appendChild(javacore_analyzer.threads.get_xml(doc))
            doc_node.appendChild(javacore_analyzer.stacks.get_xml(doc))

        doc_node.appendChild(javacore_analyzer.gc_parser.get_xml(doc))

        # Add plugin data to XML if plugins were processed
        if javacore_analyzer.plugin_data:
            try:
                logging.info("Adding plugin data to report XML")
                plugins_node = doc.createElement("plugins")
                doc_node.appendChild(plugins_node)

                for plugin_name, plugin_info in javacore_analyzer.plugin_data.items():
                    try:
                        plugin = plugin_info['plugin']
                        data = plugin_info['data']
                        logging.debug(f"Generating XML for plugin: {plugin.get_display_name()}")
                        plugin_xml = plugin.generate_xml(doc, data)
                        plugins_node.appendChild(plugin_xml)
                        logging.debug(f"Successfully added XML for plugin: {plugin.get_display_name()}")
                    except Exception as e:
                        logging.error(f"Error generating XML for plugin {plugin_name}: {e}")

                logging.info(f"Successfully added {len(javacore_analyzer.plugin_data)} plugin(s) to report XML")
            except Exception as e:
                logging.error(f"Error adding plugin data to XML: {e}")

        doc.appendChild(doc_node)

        with open(output_file, 'w', encoding='utf-8') as stream:
            doc.writexml(stream, indent="  ", addindent="  ", newl='\n', encoding="utf-8")
        doc.unlink()
        javacore_analyzer.report_xml_file = output_file

        logging.info("Finished generating report xml")

    @staticmethod
    def get_blockers_xml(javacore_analyzer, doc):
        """Build and return the <blockers> XML node.

        Args:
            javacore_analyzer: A JavacoreAnalyzer (or JavacoreSet) instance.
            doc: The minidom Document used to create nodes.

        Returns:
            Element: The populated <blockers> DOM node.
        """
        blockers_node = doc.createElement("blockers")
        count = 0
        for blocked in javacore_analyzer.blocked_snapshots:
            blocker_node = doc.createElement("blocker")
            blocker_id_node = doc.createElement("blocker_id")
            blocker_node.appendChild(blocker_id_node)
            blocker_id_node.appendChild(doc.createTextNode(str(blocked.get(0).blocker.thread.id)))
            blockers_node.appendChild(blocker_node)
            blocker_name_node = doc.createElement("blocker_name")
            blocker_node.appendChild(blocker_name_node)
            blocker_name_node.appendChild(doc.createTextNode(blocked.get(0).blocker.name))
            blocker_hash_node = doc.createElement("blocker_hash")
            blocker_node.appendChild(blocker_hash_node)
            blocker_hash_node.appendChild(doc.createTextNode(blocked.get(0).blocker.get_thread_hash()))
            blocker_size_node = doc.createElement("blocker_size")
            blocker_node.appendChild(blocker_size_node)
            blocked_size = len(blocked.get_threads_set())
            blocker_size_node.appendChild(doc.createTextNode(str(blocked_size)))
            if count > 9:
                break
            count += 1
        return blockers_node
