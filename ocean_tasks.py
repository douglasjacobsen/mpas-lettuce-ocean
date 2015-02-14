import sys, os, glob, shutil, numpy, math
import subprocess

from netCDF4 import *
from netCDF4 import Dataset as NetCDFFile
from pylab import *

from lettuce import *

from collections import defaultdict
import xml.etree.ElementTree as ET

dev_null = open(os.devnull, 'w')

def seconds_to_timestamp(seconds):#{{{
	days = 0
	hours = 0
	minutes = 0

	if seconds >= 24*3600:
		days = int(seconds/(24*3600))
		seconds = seconds - int(days * 24 * 3600)

	if seconds >= 3600:
		hours = int(seconds/3600)
		seconds = seconds - int(hours*3600)

	if seconds >= 60:
		minutes = int(seconds/60)
		seconds = seconds - int(minutes*60)

	timestamp = "%4.4d_%2.2d:%2.2d:%2.2d"%(days, hours, minutes, seconds)
	return timestamp#}}}

def timestamp_to_seconds(timestamp):#{{{
        in_str = timestamp.translate(None, "'")
	days = 0
	hours = 0
	minutes = 0
        seconds = 0
        if timestamp.find("_") > 0:
            parts = in_str.split("_")

            ymd = parts[0]
            tod = parts[1]

            if ymd.find("-") == 0:
                days = days + float(ymd)
            elif ymd.find("-") == 1:
                parts = ymd.split("-")
                days = days + 30 * float(parts[0])
                days = days + float(parts[1])
            elif ymd.find("-") == 2:
                parts = ymd.split("-")
                days = days + 365 * float(parts[0])
                days = days + 30 * float(parts[1])
                days = days + float(parts[2])
        else:
            tod = in_str

        if tod.find(":") == 0:
            seconds = float(tod)
        elif tod.find(":") == 1:
            parts = tod.split(":")
            minutes = float(parts[0])
            seconds = float(parts[1])
        elif tod.find(":") == 2:
            parts = tod.split(":")
            hours = float(parts[0])
            minutes = float(parts[1])
            seconds = float(parts[2])

        seconds = seconds + minutes * 60 + hours * 3600 + days * 24 * 3600

	return seconds#}}}

@step('A "([^"]*)" "([^"]*)" "([^"]*)" "([^"]*)" test')#{{{
def get_test_case(step, size, levs, test, time_stepper):
	if ( world.build ):
		world.basedir = os.getcwd()
		world.test = "%s_%s_%s"%(test, size, levs)
		world.num_runs = 0
		world.namelist = "namelist.ocean_forward"
		world.streams = "streams.ocean_forward"

		#Setup trusted...
		if not os.path.exists("%s/trusted_tests"%(world.basedir)):
			command = "mkdir"
			arg1 = "-p"
			arg2 = "%s/trusted_tests"%(world.basedir)
			subprocess.call([command, arg1, arg2], stdout=dev_null, stderr=dev_null)

		os.chdir("%s/trusted_tests"%(world.basedir))

		if not os.path.exists("%s/trusted_tests/%s.tgz"%(world.basedir, world.test)):
			if ( world.clone ):
				command = "wget"
				arg1 = "%s/%s.tgz"%(world.trusted_url, world.test)
				subprocess.call([command, arg1], stdout=dev_null, stderr=dev_null)

		if not os.path.exists("%s/trusted_tests/%s"%(world.basedir, world.test)):
			command = "tar"
			arg1 = "xzf"
			arg2 = "%s.tgz"%world.test
			subprocess.call([command, arg1, arg2], stdout=dev_null, stderr=dev_null)
			command = "cp"
			arg1 = "%s/namelist.ocean_forward"%world.test
			arg2 = "%s/namelist.ocean_forward.default"%world.test
			subprocess.call([command, arg1, arg2], stdout=dev_null, stderr=dev_null)
			command = "cp"
			arg1 = "%s/streams.ocean_forward.xml"%world.test
			arg2 = "%s/streams.ocean_forward.default.xml"%world.test
			subprocess.call([command, arg1, arg2], stdout=dev_null, stderr=dev_null)

		os.chdir("%s/trusted_tests/%s"%(world.basedir,world.test))
		command = "ln"
		arg1 = "-s"
		arg2 = "%s/trusted/ocean_forward_model"%(world.basedir)
		arg3 = "ocean_model_trusted"
		subprocess.call([command, arg1, arg2, arg3], stdout=dev_null, stderr=dev_null)

		command = "ln"
		arg1 = "-s"
		arg2 = "%s/testing/ocean_forward_model"%(world.basedir)
		arg3 = "ocean_model_testing"
		subprocess.call([command, arg1, arg2, arg3], stdout=dev_null, stderr=dev_null)

		command = "cp"
		arg1 = "namelist.ocean_forward.default"
		arg2 = "namelist.ocean_forward"
		subprocess.call([command, arg1, arg2], stdout=dev_null, stderr=dev_null)

		command = "cp"
		arg1 = "streams.ocean_forward.default.xml"
		arg2 = "streams.ocean_forward.xml"
		subprocess.call([command, arg1, arg2], stdout=dev_null, stderr=dev_null)

		command = "rm"
		arg1 = "-f"
		arg2 = '\*.output.nc'
		subprocess.call([command, arg1, arg2], stdout=dev_null, stderr=dev_null)

			# {{{ Setup namelist file
		namelistfile = open(world.namelist, 'r+')
		lines = namelistfile.readlines()

		for line in lines:
			if line.find("config_dt") >= 0:
				line_split = line.split(" = ")
				world.dt = line_split[1]
				world.dt_sec = timestamp_to_seconds(line_split[1])
			if line.find("config_time_integrator") >= 0:
				line_split = line.split(" = ")
				world.old_time_stepper = line_split[1].replace("'","")

		world.time_stepper_change = False
		if world.old_time_stepper.find(time_stepper) < 0:
			world.time_stepper_change = True
			if world.old_time_stepper.find("split_explicit") >= 0:
				world.dt_sec /= 10.0
			elif time_stepper.find("split_explicit") >= 0:
				world.dt_sec *= 10.0

		duration = seconds_to_timestamp(int(world.dt_sec*2))

		namelistfile.seek(0)
		namelistfile.truncate()

		for line in lines:
			new_line = line
			if line.find("config_run_duration") >= 0:
				new_line = "    config_run_duration = '%s'\n"%(duration)
			elif line.find("config_output_interval") >= 0:
				new_line = "    config_output_interval = '0000_00:00:01'\n"
			elif line.find("config_restart_interval") >= 0:
				new_line = "    config_restart_interval = '1000_00:00:01'\n"
			elif line.find("config_stats_interval") >= 0:
				new_line = "    config_stats_interval = '1000_00:00:01'\n"
			elif line.find("config_dt") >= 0:
				new_line = "    config_dt = '%s'\n"%(seconds_to_timestamp(world.dt_sec))
			elif line.find("config_frames_per_outfile") >= 0:
				new_line = "    config_frames_per_outfile = 0\n"
			elif line.find("config_write_output_on_startup") >= 0:
				new_line = "    config_write_output_on_startup = .true.\n"
			elif world.time_stepper_change:
				if line.find("config_time_integrator") >= 0:
					new_line = "    config_time_integrator = '%s'\n"%(time_stepper)

			namelistfile.write(new_line)

		namelistfile.close()

		del lines
			#}}}

		#{{{ Setup streams file
		tree = ET.parse(world.streams)
		root = tree.getroot()

		# Remove all streams (leave the immutable streams)
		for stream in root.findall('stream'):
			root.remove(stream)

		# Create an output stream
		output = ET.SubElement(root, 'stream')
		output.set('name', 'output')
		output.set('type', 'output')
		output.set('filename_template', 'output.nc')
		output.set('filename_interval', 'none')
		output.set('output_interval', '01')

		# Add tracers to output stream
		member = ET.SubElement(output, 'var_array')
		member.set('name', 'tracers')

		# Add layerThickness to output stream
		member = ET.SubElement(output, 'var')
		member.set('name', 'layerThickness')

		# Add normalVelocity to output stream
		member = ET.SubElement(output, 'var')
		member.set('name', 'normalVelocity')

		tree.write(world.streams)

		del tree
		del root
		del output
		del member
		#}}}

		os.chdir(world.basedir)

		#Setup testing...
		if not os.path.exists("%s/testing_tests"%(world.basedir)):
			command = "mkdir"
			arg1 = "-p"
			arg2 = "%s/testing_tests"%(world.basedir)
			subprocess.call([command, arg1, arg2], stdout=dev_null, stderr=dev_null)

		os.chdir("%s/testing_tests"%(world.basedir))

		if not os.path.exists("%s/testing_tests/%s.tgz"%(world.basedir, world.test)):
			if ( world.clone ):
				command = "wget"
				arg1 = "%s/%s.tgz"%(world.testing_url, world.test)
				subprocess.call([command, arg1], stdout=dev_null, stderr=dev_null)

		if not os.path.exists("%s/testing_tests/%s"%(world.basedir, world.test)):
			command = "tar"
			arg1 = "xzf"
			arg2 = "%s.tgz"%world.test
			subprocess.call([command, arg1, arg2], stdout=dev_null, stderr=dev_null)
			command = "cp"
			arg1 = "%s/namelist.ocean_forward"%world.test
			arg2 = "%s/namelist.ocean_forward.default"%world.test
			subprocess.call([command, arg1, arg2], stdout=dev_null, stderr=dev_null)
			command = "cp"
			arg1 = "%s/streams.ocean_forward.xml"%world.test
			arg2 = "%s/streams.ocean_forward.default.xml"%world.test
			subprocess.call([command, arg1, arg2], stdout=dev_null, stderr=dev_null)

		os.chdir("%s/testing_tests/%s"%(world.basedir,world.test))
		command = "ln"
		arg1 = "-s"
		arg2 = "%s/trusted/ocean_forward_model"%(world.basedir)
		arg3 = "ocean_model_trusted"
		subprocess.call([command, arg1, arg2, arg3], stdout=dev_null, stderr=dev_null)

		command = "ln"
		arg1 = "-s"
		arg2 = "%s/testing/ocean_forward_model"%(world.basedir)
		arg3 = "ocean_model_testing"
		subprocess.call([command, arg1, arg2, arg3], stdout=dev_null, stderr=dev_null)

		command = "cp"
		arg1 = "namelist.ocean_forward.default"
		arg2 = "namelist.ocean_forward"
		subprocess.call([command, arg1, arg2], stdout=dev_null, stderr=dev_null)

		command = "cp"
		arg1 = "streams.ocean_forward.default"
		arg2 = "streams.ocean_forward"
		subprocess.call([command, arg1, arg2], stdout=dev_null, stderr=dev_null)

		command = "rm"
		arg1 = "-f"
		arg2 = '\*.output.nc'
		subprocess.call([command, arg1, arg2], stdout=dev_null, stderr=dev_null)

			#{{{ Setup namelist file
		namelistfile = open(world.namelist, 'r+')
		lines = namelistfile.readlines()

		for line in lines:
			if line.find("config_dt") >= 0:
				line_split = line.split(" = ")
				world.dt = line_split[1]
				world.dt_sec = timestamp_to_seconds(line_split[1])
			if line.find("config_time_integrator") >= 0:
				line_split = line.split(" = ")
				world.old_time_stepper = line_split[1].replace("'","")

		world.time_stepper_change = False
		if world.old_time_stepper.find(time_stepper) < 0:
			world.time_stepper_change = True
			if world.old_time_stepper.find("split_explicit") >= 0:
				world.dt_sec /= 10.0
			elif time_stepper.find("split_explicit") >= 0:
				world.dt_sec *= 10.0

		duration = seconds_to_timestamp(int(world.dt_sec*2))

		namelistfile.seek(0)
		namelistfile.truncate()

		for line in lines:
			new_line = line
			if line.find("config_run_duration") >= 0:
				new_line = "    config_run_duration = '%s'\n"%(duration)
			elif line.find("config_output_interval") >= 0:
				new_line = "    config_output_interval = '0000_00:00:01'\n"
			elif line.find("config_restart_interval") >= 0:
				new_line = "    config_restart_interval = '1000_00:00:01'\n"
			elif line.find("config_stats_interval") >= 0:
				new_line = "    config_stats_interval = '1000_00:00:01'\n"
			elif line.find("config_dt") >= 0:
				new_line = "    config_dt = '%s'\n"%(seconds_to_timestamp(world.dt_sec))
			elif line.find("config_frames_per_outfile") >= 0:
				new_line = "    config_frames_per_outfile = 0\n"
			elif line.find("config_write_output_on_startup") >= 0:
				new_line = "    config_write_output_on_startup = .true.\n"
			elif world.time_stepper_change:
				if line.find("config_time_integrator") >= 0:
					new_line = "    config_time_integrator = '%s'\n"%(time_stepper)

			namelistfile.write(new_line)

		namelistfile.close()

		del lines
			#}}}

		#{{{ Setup streams file
		tree = ET.parse(world.streams)
		root = tree.getroot()

		# Remove all streams (leave the immutable streams)
		for stream in root.findall('stream'):
			root.remove(stream)

		# Create an output stream
		output = ET.SubElement(root, 'stream')
		output.set('name', 'output')
		output.set('type', 'output')
		output.set('filename_template', 'output.nc')
		output.set('filename_interval', 'none')
		output.set('output_interval', '01')

		# Add tracers to output stream
		member = ET.SubElement(output, 'var_array')
		member.set('name', 'tracers')

		# Add layerThickness to output stream
		member = ET.SubElement(output, 'var')
		member.set('name', 'layerThickness')

		# Add normalVelocity to output stream
		member = ET.SubElement(output, 'var')
		member.set('name', 'normalVelocity')

		tree.write(world.streams)

		del tree
		del root
		del output
		del member
		#}}}

		os.chdir(world.basedir)
	#}}}

