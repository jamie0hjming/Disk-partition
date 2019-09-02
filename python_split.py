#/bin/python2.7
# coding=utf8

import os
import sys
import commands
import time
import logging
import subprocess
import re

DIRNAME = os.path.dirname(os.path.realpath(__file__))

class Disk:
    """DiskInitialize"""
    __version__ = '1.0.0.0'

    def __init__(self,splits):
        if splits=="0":
            self.splits=""
        else:
            #self.splits = sorted(splits.split(','), reverse=True)
            self.splits = splits.split(',')
        self.split_dir_name = dict()
        for split in self.splits:
            self.split_dir_name[split] = 0

        self.md_num = 0

        self.disk_num = self.get_disk_num()
        self.disk = self.get_disk_info()

    def get_disk_num(self):
        '''
        count the disk num
        '''
        cmd = "lsblk | grep disk |grep -v sda |wc -l"
        (status, output) = commands.getstatusoutput(cmd)
        if status == 0:
            return output
        else:
            logging.error("get_disk_num error")
            sys.exit(1)

    def get_disk_info(self):
        '''
        scan disk and get the detail
        '''
        cmd = "lsblk | grep disk | grep -vE \"NAME|sda|-\" |awk '{print $1;print $4;}'"
        (status, output) = commands.getstatusoutput(cmd)
	#print output
        disk = dict()
        sum_nvme0 = "lsblk | grep nvme0 | wc -l"
        (status,sum_nvme0) = commands.getstatusoutput(sum_nvme0)
	print sum_nvme0
        self.sum_nvme0 = int(sum_nvme0)
        if int(sum_nvme0) > 2 :
            for i,v in enumerate(output.split('\n')):
		print i
		print v
                if ( i % 2 ) == 0:
                    disk_tag = v
                    name = "/dev/"+v
                    disk[disk_tag] = dict()
                    disk[disk_tag]['name'] = name
                    disk[disk_tag]['used'] = 0
                    disk[disk_tag]['partition'] = 0
                    disk[disk_tag]['in_use'] = 0 # 0 or 1
                    (start,end)= self.get_disk_sectors_nvme0()
                    if 'nvme0' in name:
                        disk[disk_tag]['left'] = int(end) - int(start)
                        disk[disk_tag]['begin'] = int(start) + 1
                        disk[disk_tag]['sectors'] = disk[disk_tag]['left'] - disk[disk_tag]['begin']
                    else:
                        disk[disk_tag]['sectors'] = int(self.get_disk_sectors(name))
                        disk[disk_tag]['left'] = disk[disk_tag]['sectors'] - 2048
                        disk[disk_tag]['begin'] = 2048
                else:
                    if i == 1:
                        if 'T' in v:
                            disk[disk_tag]['cap'] = float(v.replace('T',''))* 1000 - 60
                        else:
                            disk[disk_tag]['cap'] = float(v.replace('G','')) - 60
                    else:
                        if 'T' in v:
                            disk[disk_tag]['cap'] = float(v.replace('T',''))*1000
                        else:
                            disk[disk_tag]['cap'] = float(v.replace('G',''))
        else:
	    print "-----------"
            print output.split('\n')
	    print "----------------"
            for i,v in enumerate(output.split('\n')):
		print i
		print v
                if ( i % 2 ) == 0:
                    disk_tag = v
                    name = "/dev/"+v
                    disk[disk_tag] = dict()
                    disk[disk_tag]['name'] = name
                    disk[disk_tag]['used'] = 0
                    disk[disk_tag]['partition'] = 0
                    disk[disk_tag]['in_use'] = 0 # 0 or 1
                    disk[disk_tag]['sectors'] = int(self.get_disk_sectors(name))
                    disk[disk_tag]['left'] = disk[disk_tag]['sectors'] - 2048
                    disk[disk_tag]['begin'] = 2048
                else:
                    if 'T' in v:
                        disk[disk_tag]['cap'] = float(v.replace('T',''))*1000
                    else:
                        disk[disk_tag]['cap'] = float(v.replace('G',''))
        print "-------------disk info---------------"
        print disk
        return disk

    def get_disk_sectors_nvme0(self):
        start = "fdisk -l | grep \"/dev/nvme0n1p7\" | awk -F \" \" '{print $3}'"
        end = "fdisk -l | grep nvme0 |grep Disk | grep -vE \"identifier|Disklabel\" |cut -d\",\" -f3|awk {'print $1'}"
        (status,start) = commands.getstatusoutput(start)
        if status != 0:
            print "get sector error: %s" % disk_name
            sys.exit(1)
        (status,end) = commands.getstatusoutput(end)
        if status != 0:
            print "get sector error: %s" % disk_name
            sys.exit(1)
        return start,end

    def get_disk_sectors(self,disk_name):
        cmd = "fdisk -l %s |grep Disk | grep -vE \"identifier|Disklabel\" |cut -d\",\" -f2|awk {'print $1'}" \
            % (disk_name)
        (status, output) = commands.getstatusoutput(cmd)
        if status != 0:
            print "get sector error: %s" % disk_name
            sys.exit(1)
        sectors_num = int(output.split()[-1])/512
        return sectors_num

    def get_disk_max_left(self):
        max_left = 0
        for disk_tag,disk_detal in enumerate(self.disk):
            if disk_detail['left'] > max_left:
                max_left = disk_detail['left']
                max_disk = disk_tag
        return disk_tag

    def umountfs(self):
        """umount the point already exist
        the point expcet home var noah etc will be unmounted
        """

        print "-----------------umount points---------------------"
        cmd = "df -h |grep -vE \"Filesystem|tmpfs|sda|nvme0n1p\"|awk '{print $6}'"
        (status, output) = commands.getstatusoutput(cmd)
        if status != 0:
            print "umount fs 1: get mount point error"
            sys.exit(1)
        if output != "":
            for point in output.split("\n"):
                umount_cmd = "umount %s" % point
                print umount_cmd + ":"
                (status, output) = commands.getstatusoutput(umount_cmd)
                if status != 0:
                    print "umount fs: umount_cmd %s error" % (umount_cmd)
                    sys.exit(1)
                print "ok"
        (status, output) = commands.getstatusoutput("df -h |grep -E \"/home/ssd\"|awk '{print $6}'")
        if status != 0:
            print "umount fs 2: get mount point error"
            sys.exit(1)
        if output != "":
            umount_cmd = "umount %s" % output
            print umount_cmd + ":"
            (status, output) = commands.getstatusoutput(umount_cmd)
            if status != 0:
                print "umount fs: umount_cmd %s error" % (umount_cmd)
                #sys.exit(1)
            print "ok"
        print "---------------umount points finished-------------------"
        return 0

    def clear_partition(self):
        """clear the partition already exist
        the partition except sda will be unmounted
        """

        print "------------------begin to clear lvm----------------------"
        find_vg = "vgs | grep -v VG| grep -v \"No volume groups found\" | awk '{print $1}'"
        (status, output) = commands.getstatusoutput(find_vg)
        if output.strip()=="No volume groups found":
            print "-------------------vg has been cleared------------------------"
        else:
            for vg in output.split("\n"):
                if vg == "":
                    print "vg has been cleared"
                    break
                rm_vg = "vgremove -f %s" % (vg)
                (status, output) = commands.getstatusoutput(rm_vg)
                if status != 0:
                    print output
                    print "vg remove error"
                    sys.exit(1)

        find_pv = "pvs | grep -v PV | awk '{print $1}'"
        (status, output) = commands.getstatusoutput(find_pv)
        for pv in output.split("\n"):
            if pv == "":
                print "pv has been cleared"
                break
            rm_pv = "pvremove %s" % (pv)
            (status, output) = commands.getstatusoutput(rm_pv)
            if status != 0:
                print "pv remove error"
                sys.exit(1)
        print "-------------------lvm has been cleared------------------------"
        """
        find_mdadm = "mdadm --detail --scan | awk {'print $2'}"
        (status, output) = commands.getstatusoutput(find_mdadm)
        for mdadm in output.split("\n"):
            if mdadm=="":
                print "mdadm has been cleared : %s" % (mdadm)
                break
            if re.match("Unknown keyword",mdadm) != None:
                continue
            mdadm_name = mdadm
            stop_mdadm = "mdadm --stop %s" % (mdadm_name)
            (status, output) = commands.getstatusoutput(stop_mdadm)
            if status != 0:
                print "stop mdadm error: %s" % (stop_mdadm)
                sys.exit(1)
            remove_mdadm = "mdadm --remove %s" % (mdadm_name)
            (status, output) = commands.getstatusoutput(remove_mdadm)
            if status != 0:
                print "remove mdadm error: %s" % (remove_mdadm)
                sys.exit(1)
        """

        print "------------------begin to clear partition----------------------"
        for disk in self.disk:
            disk_name = self.disk[disk]["name"]
            find_partition = "parted -s %s p | grep -vE \"Inventec|Disk|Sector|Partition|Number|Model\" |awk '{print $1}' |sed '/^$/d'" % (disk_name)
            (status, output) = commands.getstatusoutput(find_partition)
            disk_partition =  output.split("\n")
            for partition in disk_partition:
                if partition=="":
                    print "partition has been cleared : %s" % (partition)
                    break
                rm_partiton = "parted -s %s rm %s" % (disk_name,partition)
                (status, output) = commands.getstatusoutput(rm_partiton)
                if status != 0:
                    print "clear partition: rm partition %s error" % (rm_partiton)
                    #sys.exit(1)
            '''mklable gpt for every disk'''
            cmd_fix = "parted -s %s mklabel gpt" % (disk_name)
            (status, output) = commands.getstatusoutput(cmd_fix)
            if status != 0:
                print "disk mklabel error: %s" % (cmd_fix)
                #sys.exit(1)
        print "------------------partition has been cleared----------------------"

        return 0

    def mk_fs(self,partition_name):
        print "make fs for %s" % (partition_name)
        cmd_mkfs = "mkfs.ext4 -m 0 %s" % (partition_name)
        print "make fs : %s" % (cmd_mkfs)
        (status, output) = commands.getstatusoutput(cmd_mkfs)
        if status != 0 :
            print "mkfs error: %s" % (cmd_mkfs)
            sys.exit(1)
        return 0

    def mk_big_fs(self,partition_name):
        print "make fs for %s" % (partition_name)
        cmd_mkfs = "/root/ini_scripts/e2fsprogs-1.42.9/misc/mke2fs -O 64bit,has_journal,extents,huge_file,flex_bg,uninit_bg,dir_nlink,extra_isize \
        -i 4194304 %s" % (partition_name)
        print "make fs : %s" % (cmd_mkfs)
        (status, output) = commands.getstatusoutput(cmd_mkfs)
        if status != 0 :
            print "mkfs error: %s" % (cmd_mkfs)
            sys.exit(1)
        return 0


    def mk_part(self, disk_tag, cap):
        disk_name = self.disk[disk_tag]['name']
        begin_s = int(self.disk[disk_tag]['begin'])
        print cap
        end_s = int(self.disk[disk_tag]['begin']) + cap*1024*1024*1024/512
        print "end_s: %s" % (end_s)
        cmd_mk_part = "parted -s %s mkpart ext4 %ss %ss" \
                    % (disk_name,begin_s,end_s)
        (status, output) = commands.getstatusoutput(cmd_mk_part)
        if status != 0:
            print "disk mkpart error: %s" % (cmd_mk_part)
            sys.exit(1)

        print cmd_mk_part
        self.disk[disk_tag]['in_use'] = 1
        self.disk[disk_tag]['begin'] = end_s+1
        self.disk[disk_tag]['left'] = self.disk[disk_tag]['left'] - cap*1024*1024*1024/512
        self.disk[disk_tag]['partition'] = self.disk[disk_tag]['partition'] + 1

        if re.match("/dev/nvme",disk_name) != None: #nvme's partition name differs from sdbcde
            partition_name = disk_name + "p" + str(self.disk[disk_tag]['partition'])
        else:
            partition_name = disk_name+str(self.disk[disk_tag]['partition'])
        while 1:
            cmd_check = "ls %s |wc -l" % (partition_name)
            (status, output) = commands.getstatusoutput(cmd_check)
            if output != "1":
                print output
                time.sleep(3)
                continue
            else:
                print "the partition %s exist" % partition_name
                break

        print "finish"
        return partition_name

    def mk_part_multi(self, cap):
        """make soft raid with multi disk
        """
        device_num = 0
        device_name = ""
        disk_cap_wanted = cap
        for disk_tag in self.disk:
            #disk_name = self.disk[disk_tag]['name']
            if self.disk[disk_tag]['left'] < 83886080:
                continue
            disk_left_G = self.disk[disk_tag]['left']/2/1024/1024
            print "disk_left_G: %s" % (disk_left_G)
            print "disk_cap_wanted: %s" % (disk_cap_wanted)
            if disk_left_G <= disk_cap_wanted:
                partition_name = self.mk_part(disk_tag, disk_left_G)
                device_num = device_num + 1
                device_name = device_name + partition_name + " "
                disk_cap_wanted = disk_cap_wanted - disk_left_G
            else:
                partition_name = self.mk_part(disk_tag, disk_cap_wanted)
                device_num = device_num + 1
                device_name = device_name + partition_name + " "
                disk_cap_wanted = 0
            if disk_cap_wanted == 0:
                break
        if disk_cap_wanted == 0:
            print "make mdadm by using : %s" % (device_name)
            mdadm_name = "/dev/md%s" % self.md_num
            cmd_stopmdadm = "mdadm --stop %s" % (mdadm_name)
            (status, output) = commands.getstatusoutput(cmd_stopmdadm)

            cmd_mdadm = "echo y | mdadm --create %s --level=0 --raid-devices=%s %s" \
                % (mdadm_name, device_num, device_name)
            (status, output) = commands.getstatusoutput(cmd_mdadm)
            if status != 0:
                print "mdadm error: %s" % (cmd_mdadm)
                sys.exit(1)
            self.md_num = self.md_num + 1
        else:
            print "we do not have enough cap %s" % (cap)
            sys.exit(1)
        return mdadm_name

    def mk_proxy_part_multi(self):
        device_num = 0
        device_name = ""
        print "he bing proxy"
        for disk_tag in self.disk:
            disk_left_G = self.disk[disk_tag]['left']/2/1024/1024
            if disk_left_G >= 10:
                partition_name = self.mk_part(disk_tag, disk_left_G)
                print "---"
                if self.sum_nvme0 > 2 and partition_name == '/dev/nvme0n1p2':
                    partition_name = '/dev/nvme0n1p8'
                print partition_name
                device_num = device_num + 1
                print "------"
                print device_num
                print "-------------"
                device_name = device_name + partition_name + " "
                print device_name
        if device_num > 1:
            mdadm_name = "/dev/md%s" % self.md_num
            cmd_mdadm = "echo y | mdadm --create %s --level=0 --raid-devices=%s %s" \
                % (mdadm_name, device_num, device_name)
            (status, output) = commands.getstatusoutput(cmd_mdadm)
            if status != 0:
                print "mdadm error: %s" % (cmd_mdadm)
                sys.exit(1)
        elif device_num == 1:
            print "----------------------------"
            mdadm_name = device_name
            print mdadm_name
        else:
            print "we do not have enough cap for dbproxy"
            mdadm_name = ""

        return mdadm_name

    def mk_mountpoint(self,split):
        print "make mountpoint for split:%s" % (split)
        split_num = self.split_dir_name[split]
        self.split_dir_name[split] = split_num+1
        mountpoint = "/data/xdb-ssd-x-%s00g-%s" % (split,split_num)
        cmd_mkdir = "mkdir -p %s" % (mountpoint)
        (status, output) = commands.getstatusoutput(cmd_mkdir)
        if status != 0 :
            print "mkdir error: %s" % (cmd_mkdir)
            sys.exit(1)
        return mountpoint

    def mk_proxy_mtpoint(self):
        mountpoint = "/data/xdb-ssd-s-dbproxy"
        cmd_mkdir = "mkdir -p %s" % (mountpoint)
        (status, output) = commands.getstatusoutput(cmd_mkdir)
        if status != 0 :
            print "mkdir error: %s" % (cmd_mkdir)
            sys.exit(1)
        return mountpoint


    def mount(self,partition_name,mountpoint):
        cmd_mount = "mount -o nobarrier -t ext4 %s %s" % (partition_name,mountpoint)
        (status, output) = commands.getstatusoutput(cmd_mount)
        if status != 0:
            print "mount error: %s" % (cmd_mount)
            sys.exit(1)

    def disk_initial_basic(self):
        '''
        for only one disk
        '''
        for disk_tag in self.disk:
            disk_name = self.disk[disk_tag]['name']

        for split in self.splits:
            if split=="":
                continue
            print "-----------------make split:%s---------------------" % (split)
            partition_name = self.mk_part(disk_tag,int(split)*100)

            self.mk_fs(partition_name)

            mountpoint = self.mk_mountpoint(split)

            self.mount(partition_name,mountpoint)

        disk_left = int(self.disk[disk_tag]['left']*512/1024/1024/1024)
        if disk_left > 60:
            actual_split = disk_left
            partition_name = self.mk_part(disk_tag, disk_left)

            self.mk_fs(partition_name)

            mountpoint = self.mk_proxy_mtpoint()

            self.mount(partition_name,mountpoint)

        return 0

    def disk_initial_multi(self):
        #return 0
        '''
        for multi disk
        '''
        print "---------disk initial for multi disk------------"

        for split in self.splits:
            if split=="" or split==0:
                continue

            print "---------------deal with the split:%s-------------" % (split)
            split_success = 0

            for disk_tag in self.disk:
                if self.disk[disk_tag]['left'] < 41943040:
                    continue
                print self.disk[disk_tag]['left']
                print int(split)*100*1024*1024*2
                if self.disk[disk_tag]['left'] >= int(split)*100*1024*1024*2:
                    partition_name = self.mk_part(disk_tag,int(split)*100)
                    print "------------"
                    print partition_name
                    split_success = 1
                    self.mk_fs(partition_name)
                    mountpoint = self.mk_mountpoint(split)
                    print "22222222"
                    print mountpoint
                    self.mount(partition_name,mountpoint)
                    break

            if split_success == 0: #bigger than one disk
                partition_name = self.mk_part_multi(int(split)*100)
                print partition_name
                #self.mk_fs(partition_name)
                self.mk_big_fs(partition_name)

                mountpoint = self.mk_mountpoint(split)

                self.mount(partition_name, mountpoint)


        print "deal with to merge proxy"

        dbproxy_partition_name = self.mk_proxy_part_multi()
        if dbproxy_partition_name != "" :

            self.mk_big_fs(dbproxy_partition_name)

            mountpoint = self.mk_proxy_mtpoint()

            self.mount(dbproxy_partition_name, mountpoint)

        return 0

    def refresh_mdadm(self):
        cmd = "mdadm --detail --scan | " \
            "sed -r -e 's/,/ /g' -e 's/ +devices=/DEVICE /' -e 's/ UUID/\\nUUID/' > /etc/mdadm.conf"
        (status, output) = commands.getstatusoutput(cmd)
        if status != 0 :
            print "refresh mdadm.conf error"
            sys.exit(1)
        return 0

    def refresh_fstab(self):
        (status, output) = commands.getstatusoutput("cp /etc/fstab /etc/fstab.bak")
        if status != 0 :
            print "refresh fstab error: cp /etc/fstab /etc/fstab.bak"
            sys.exit(1)
        (status, output) = commands.getstatusoutput("cp -f /etc/mtab /etc/fstab")
        if status != 0 :
            print "refresh fstab error: cp -f /etc/mtab /etc/fstab"
            sys.exit(1)
        return 0

    def disk_initial(self):
        self.umountfs()
        self.clear_partition()
        if self.disk_num == 1:
            self.disk_initial_basic()
            self.refresh_fstab()
            return 0
        else:
            print self.disk_num
            self.disk_initial_multi()
            self.refresh_fstab()
            self.refresh_mdadm()
            return 0

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Usage: HostsServier.py ${the_split_you_want}"
        sys.exit(-1)
    splits = sys.argv[1]
    disk = Disk(splits)
    print "begin"python
    disk.disk_initial()
    print "split success"
df 