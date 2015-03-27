#############################################################################
# 
# Copyright (C) Zenoss, Inc. 2010, all rights reserved.
# 
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
# 
##############################################################################

ESAHOME=$(PWD)

default: egg

egg: clean
	@rm -f dist/*.egg
	@python setup.py bdist_egg

clean:
	@rm -rf $(ESAHOME)/dist
	@rm -rf $(ESAHOME)/build
	@rm -rf $(ESAHOME)/*.egg-info

