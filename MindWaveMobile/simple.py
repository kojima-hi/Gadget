#!/usr/bin/env python
# -*- coding: utf-8 -*-
from copy import deepcopy
import re
import sys
import time
import argparse
import thinkgear
PORT = '/dev/tty.MindWaveMobile-SerialPo'


class Signal:
    def __init__(self, quality_threshold=30, output_file='signal.out', measurement_time=1):
        # inform
        print('output file:              {}'.format(output_file))
        print('measurement time (min):   {}'.format(measurement_time))
        print('signal quality threshold: {}'.format(quality_threshold))

        # var
        self.quality_threshold = quality_threshold
        self.output_file = output_file
        self.measurement_time = float(measurement_time * 60)
        self.start_time = time.time()

        # packet types
        self.signal_quality_types = ['POOR']
        self.signal_wave_types = ['delta', 'theta', 'lowalpha', 'highalpha', 'lowbeta', 'highbeta', 'lowgamma', 'midgamma']
        self.signal_state_types = ['ATTENTION', 'MEDITATION']

        # for store
        self.direct_types = deepcopy(self.signal_quality_types)
        self.direct_types.extend(self.signal_state_types)

        self.initialize()
        self.initialize_output()

    def initialize(self):
        self.is_stored = False
        self.signal_dict = {}
        for signal_types in [self.signal_quality_types, self.signal_wave_types, self.signal_state_types]:
            for signal_type in signal_types:
                self.signal_dict[signal_type] = -1
        return

    def initialize_output(self):
        with open(self.output_file, 'w') as f:
            f.write('# ')
            count = 0
            for signal_types in [self.signal_quality_types, self.signal_wave_types, self.signal_state_types]:
                for signal_type in signal_types:
                    count += 1
                    f.write('{}.{}, '.format(count, signal_type))
            f.write('\n')
        return

    def store(self, packet):
        is_stored = False
        for signal_type in self.direct_types:
            if signal_type in packet:
                val = (packet.split())[-1]
                self.signal_dict[signal_type] = int(val)
                is_stored = True
        
        if not is_stored:
            if 'EEGPowerData' in packet:
                for signal_type in self.signal_wave_types:
                    pattern = '.*{}=(\d+).*'.format(signal_type)
                    val = (re.match(pattern, packet)).group(1)
                    self.signal_dict[signal_type] = int(val)
            else:
                print('Warning: Unknown signal')
        return

    def check_stored(self):
        is_stored = True
        for key, val in (self.signal_dict).items():
            if val < 0:
                is_stored = False
        return is_stored

    def output(self):
        if self.signal_dict['POOR'] < self.quality_threshold:
            with open(self.output_file, 'a') as f:
                for signal_types in [self.signal_quality_types, self.signal_wave_types, self.signal_state_types]:
                    for signal_type in signal_types:
                        f.write('{} '.format(self.signal_dict[signal_type]))
                        #sys.stdout.write('{} '.format(signal_type))
                f.write('\n')
            print('stored. {:3d}, {:3d} (ATT, MED)'.format(self.signal_dict['ATTENTION'], self.signal_dict['MEDITATION']))
        else:
            print('not stored: poor signal {}'.format(self.signal_dict['POOR']))

        self.initialize()
        return

    def check_end(self):
        is_end = False
        if (time.time() - self.start_time) > self.measurement_time:
            is_end = True
        return is_end


def get_parse():
    parser = argparse.ArgumentParser()

    parser.add_argument('-o', '--output', type=str, required=True,
                        help='output file for store signal')
    parser.add_argument('-m', '--measurement', type=int, default=1,
                        help='measurement time (min)')

    return parser.parse_args()


def work(output_file, measurement_time):
    signal = Signal(output_file=output_file, measurement_time=measurement_time)
    is_end = False
    for packets in thinkgear.ThinkGearProtocol(PORT).get_packets():
        for packet in packets:
            if isinstance(packet, thinkgear.ThinkGearRawWaveData):
                continue

            signal.store(str(packet))
            if signal.check_stored():
                signal.output()
                is_end = signal.check_end()

        if is_end:
            break


def main():
    args = get_parse()
    work(args.output, args.measurement)
    return


if __name__ == "__main__":
    main()
