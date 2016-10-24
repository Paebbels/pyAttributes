# EMACS settings: -*-  tab-width: 2; indent-tabs-mode: t -*-
# vim: tabstop=2:shiftwidth=2:noexpandtab
# kate: tab-width 2; replace-tabs off; indent-width 2;
# 
# =============================================================================
#                 _   _   _        _ _           _       
#  _ __  _   _   / \ | |_| |_ _ __(_) |__  _   _| |_ ___ 
# | '_ \| | | | / _ \| __| __| '__| | '_ \| | | | __/ _ \
# | |_) | |_| |/ ___ \ |_| |_| |  | | |_) | |_| | ||  __/
# | .__/ \__, /_/   \_\__|\__|_|  |_|_.__/ \__,_|\__\___|
# |_|    |___/                                           
# 
# =============================================================================
# Authors:						Patrick Lehmann
# 
# Python Executable:	pyAttribute Testcase 1
#
# Description:
# ------------------------------------
#		TODO
#
# License:
# ============================================================================
# Copyright 2007-2015 Patrick Lehmann - Dresden, Germany
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#		http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================

class Attribute():
	AttributesMemberName =	"__attributes__"
	_debug =								False
	
	def __call__(self, func):
		# inherit attributes and append myself or create a new attributes list
		if (func.__dict__.__contains__(Attribute.AttributesMemberName)):
			func.__dict__[Attribute.AttributesMemberName].append(self)
		else:
			func.__setattr__(Attribute.AttributesMemberName, [self])
		return func
	
	def __str__(self):
		return self.__name__

	@classmethod
	def GetAttributes(self, method):
		if method.__dict__.__contains__(Attribute.AttributesMemberName):
			attributes = method.__dict__[Attribute.AttributesMemberName]
			if isinstance(attributes, list):
				return [attribute for attribute in attributes if isinstance(attribute, self)]
		return list()

class DefaultAttribute(Attribute):
	__handler =	None
	
	def __call__(self, func):
		self.__handler = func
		return super().__call__(func)
	
	@property
	def Handler(self):
		return self.__handler
		
class CommandAttribute(Attribute):
	__command =	""
	__handler =	None
	__kwargs =	None

	def __init__(self, command, **kwargs):
		super().__init__()
		self.__command =	command
		self.__kwargs =		kwargs
	
	def __call__(self, func):
		self.__handler = func
		return super().__call__(func)
	
	@property
	def Command(self):
		return self.__command
		
	@property
	def Handler(self):
		return self.__handler
	
	@property
	def KWArgs(self):
		return self.__kwargs
		
class ArgumentAttribute(Attribute):
	__args =		None
	__kwargs =	None

	def __init__(self, *args, **kwargs):
		super().__init__()
		self.__args =		args
		self.__kwargs =	kwargs
	
	@property
	def Args(self):
		return self.__args
	
	@property
	def KWArgs(self):
		return self.__kwargs
	
class SwitchArgumentAttribute(ArgumentAttribute):
	def __init__(self, *args, **kwargs):
		kwargs['action'] =	"store_const"
		kwargs['const'] =		True
		kwargs['default'] =	False
		super().__init__(*args, **kwargs)


class MyBase():
	def __init__(self):
		pass

class AttributeHelperMixin():
	def GetMethods(self):
		return {funcname: func
						for funcname, func in self.__class__.__dict__.items()
						if hasattr(func, '__dict__')
					 }.items()

	def HasAttribute(self, method):
		if method.__dict__.__contains__(Attribute.AttributesMemberName):
			attributeList = method.__dict__[Attribute.AttributesMemberName]
			return (isinstance(attributeList, list) and (len(attributeList) != 0))
		else:
			return False
				
	def GetAttributes(self, method):
		if method.__dict__.__contains__(Attribute.AttributesMemberName):
			attributeList = method.__dict__[Attribute.AttributesMemberName]
			if isinstance(attributeList, list):
				return attributeList
		return list()
	
class ArgParseMixin(AttributeHelperMixin):
	__mainParser = 	None
	__subParser =		None
	__subParsers =	{}

	def __init__(self, **kwargs):
		super().__init__()
		
		# create a commandline argument parser
		import argparse
		self.__mainParser = argparse.ArgumentParser(**kwargs)
		self.__subParser = self.__mainParser.add_subparsers(help='sub-command help')
		
		for funcname,func in self.GetMethods():
			defAttributes = DefaultAttribute.GetAttributes(func)
			if (len(defAttributes) != 0):
				defAttribute = defAttributes[0]
				self.__mainParser.set_defaults(func=defAttribute.Handler)
				continue
			
			cmdAttributes = CommandAttribute.GetAttributes(func)
			if (len(cmdAttributes) != 0):
				cmdAttribute = cmdAttributes[0]
				subParser = self.__subParser.add_parser(cmdAttribute.Command, **(cmdAttribute.KWArgs))
				subParser.set_defaults(func=cmdAttribute.Handler)
				
				for argAttribute in ArgumentAttribute.GetAttributes(func):
					subParser.add_argument(*(argAttribute.Args), **(argAttribute.KWArgs))

				self.__subParsers[cmdAttribute.Command] = subParser
				continue
	
	def Run(self):
		# parse command line options and process splitted arguments in callback functions
		args = self.__mainParser.parse_args()
		# because func is a function (unbound to an object), it MUST be called with self as a first parameter
		args.func(self, args)
	
	@property
	def MainParser(self):
		return self.__mainParser
	
	@property
	def SubParsers(self):
		return self.__subParsers


class prog(MyBase, ArgParseMixin):
	def __init__(self):
		import argparse
		import textwrap
		
		# call constructor of the main interitance tree
		MyBase.__init__(self)
		
		# Call the constructor of the ArgParseMixin
		ArgParseMixin.__init__(self,
			# prog =	self.program,
			# usage =	"Usage?",			# override usage string
			description = textwrap.dedent('''\
				This is the Admin Service Tool.
				'''),
			epilog =	"Epidingsbums",
			formatter_class = argparse.RawDescriptionHelpFormatter,
			add_help=False)

		self.MainParser.add_argument('-v', '--verbose',	dest="verbose",	help='print out detailed messages',	action='store_const', const=True, default=False)
		self.MainParser.add_argument('-d', '--debug',		dest="debug",		help='enable debug mode',						action='store_const', const=True, default=False)
	
	def Run(self):
		ArgParseMixin.Run(self)
	
	@DefaultAttribute()
	def HandleDefault(self, args):
		print("DefaultHandler: verbose={0}  debug={1}".format(str(args.verbose), str(args.debug)))
	
	@CommandAttribute('help', help="help help")
	def HandleHelp(self, args):
		print("HandleHelp:")
	
	@CommandAttribute("prog", help="my new command")
	@ArgumentAttribute(metavar='<DeviceID>', dest="DeviceID", type=str, help='todo help')
	@ArgumentAttribute(metavar='<BitFile>', dest="Filename", type=str, help='todo help')
	def HandleProg(self, args):
		print("HandleProg: DeviceID={0}  BitFile={1}".format(args.DeviceID, args.Filename))
	
	@CommandAttribute("list", help="my new command")
	@SwitchArgumentAttribute('--all', dest="all", help='show all devices, otherwise only available')
	def HandleList(self, args):
		print("HandleList: all={0}".format(str(args.all)))
	
p = prog()
p.Run()

