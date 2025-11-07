#
# Copyright IBM Corp. 2025 - 2025
# SPDX-License-Identifier: Apache-2.0
#

import pandas as pd
import numpy as np


def main():
    df = pd.read_csv('data.csv', delimiter='\t')
    print(df)
    for index, row in df.iterrows():
        if not np.isfinite(row['stack_trace_depth']):
            stack_trace = row['stack_trace']
            #print("Index: " + str(index) + " stack trace: " + stack_trace)
            if isinstance(stack_trace, str):
                depth = stack_trace.count('.java:') + stack_trace.count('Native Method')
            else:
                depth = 0
            row['stack_trace_depth'] = depth
            df.loc[index, 'stack_trace_depth'] = depth
    print(df)
    df.to_csv('data-modified.csv', sep='\t')

if __name__ == '__main__':
    main()