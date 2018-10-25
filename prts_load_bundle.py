#!/usr/bin/python

'''
Author: 
    Proteas
Date:
    2018-10-22
Purpose:
    load bundle to process
Usage:
    add the following line to ~/.lldbinit
    command script import ~/.lldb/prts_load_bundle.py
'''

import lldb
import os
import shlex

# helper for define static variables
def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate
# --------------------------------------------------------------------------------------------------

def __lldb_init_module (debugger, dict):
    debugger.HandleCommand('command script add -f prts_load_bundle.prts_load_bundle prts_load_bundle')
    print 'The "prts_load_bundle" command has been installed'
# --------------------------------------------------------------------------------------------------

def create_command_arguments(command):
    return shlex.split(command)
# --------------------------------------------------------------------------------------------------

@static_vars(moduleNameSuffix = 0)
def prts_load_bundle(debugger, command, result, dict):
    args = create_command_arguments(command)

    if len(args) != 1:
        print "prts_load_bundle path-of-bundle"
        return

    bundlePath = args[0]
    print "[+] bundle: %s" % (bundlePath)

    prts_load_bundle.moduleNameSuffix += 1
    moduleName = "PRTS_Bundle-%d" % (prts_load_bundle.moduleNameSuffix)
    print "[+] module: %s" % (moduleName)

    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    thread = process.GetSelectedThread()
    frame = thread.GetSelectedFrame()

    exprOpt = lldb.SBExpressionOptions()
    exprOpt.SetIgnoreBreakpoints(True)
    exprOpt.SetTrapExceptions(False)
    exprOpt.SetFetchDynamicValue(lldb.eDynamicCanRunTarget)
    exprOpt.SetTimeoutInMicroSeconds(30 * 1000 * 1000)  # 30 second timeout
    exprOpt.SetTryAllThreads(True)
    exprOpt.SetUnwindOnError(True)
    exprOpt.SetGenerateDebugInfo(True)
    exprOpt.SetCoerceResultToId(True)
    # eLanguageTypeObjC, eLanguageTypeObjC_plus_plus, eLanguageTypeSwift
    exprOpt.SetLanguage(lldb.eLanguageTypeObjC_plus_plus)

    exprStr = ' \
    unsigned long long libHandle = 0; \n\
    do { \n\
        id bundleData = [NSData dataWithContentsOfFile:@"%s"]; \n\
        if (bundleData == 0) { \n\
            NSLog(@"[-] load bundle data"); \n\
            break; \n\
        } \n\
        else { \n\
            // NSLog(@"[+] bundle: 0x%%016llx", (unsigned long long)[bundleData bytes]); \n\
        } \n\
        unsigned long long bundleHandle = 0; \n\
        int ret = (int)NSCreateObjectFileImageFromMemory((void *)[bundleData bytes], (unsigned)[bundleData length], (void *)&bundleHandle); \n\
        if (ret != 1) { \n\
            NSLog(@"[-] NSCreateObjectFileImageFromMemory: 0x%%x", ret); \n\
            break; \n\
        } \n\
        else { \n\
            // NSLog(@"[+] bundle handle: 0x%%016llx", bundleHandle); \n\
        } \n\
        libHandle = (unsigned long long)NSLinkModule(bundleHandle, "%s", 0); \n\
        if (libHandle == 0) { \n\
            NSLog(@"[-] NSLinkModule"); \n\
            break; \n\
        } \n\
        else { \
            // NSLog(@"[+] module: 0x%%016llx", libHandle); \n\
        } \n\
    } while (false); \n\
    libHandle; \n\
    ' % (bundlePath, moduleName)
    # print exprStr

    exprSBVal = None
    if frame.IsValid():
        exprSBVal = frame.EvaluateExpression(exprStr, exprOpt)
    else:
        exprSBVal = target.EvaluateExpression(exprStr, exprOpt)

    # print exprSBVal
    if exprSBVal.error.Success():
        libHandle = lldb.value(exprSBVal)
        print "[+] module: 0x%016x" % (libHandle)
    else:
        print "[-] fail to load module"
# --------------------------------------------------------------------------------------------------
