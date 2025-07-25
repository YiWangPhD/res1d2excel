#!/usr/bin/env python
# coding: utf-8

# Author: Yi Wang
# common utilites


import re
import ast
import hashlib


def accept_check():
    message = """
    This software is provided for study purpose only. 
    Author is not liable for any damage. 
    Type in your full name to accpet this disclaimer. 
    """
    print(message)
    name = input("Enter Your Full Name:")
    name = name.strip().lower().encode()
    m = hashlib.sha256()
    m.update(name)
    if m.hexdigest() in ['34b68efed6593b5e6e1807b8f17a6b2a35255feb07cae2752c664a205b19ab5f', 
                         '63e9eb8368f84c740170828a9641d3e1a9438e7a6d90504c6a36944dd6d9ab3d']:
        return True
    else:
        return False


def common_string(strings, rev = False):
    """
    find common section in multiple strings. start from beginning (rev = False) or end (rev = True)
    :param strings: list of strings
    :param rev: False from left side, True from right side reversed.
    :return: common string
    """
    if not isinstance(strings, list):
        print('not list')
        return ''
    if not all ([isinstance(string, str) for string in strings]):
        return ''
    if any([len(string) == 0 for string in strings]):
        return ''
    if len(strings) < 2:
        return ''
    if len(strings) == 2:
        [a, b] = strings
        minLen = min(len(a), len(b))
        if rev:
            a = a[::-1]
            b = b[::-1]
            for i in range(minLen):
                if a[i] != b[i]:
                    return a[:i][::-1]
            return a[:minLen][::-1]
        else:
            for i in range(minLen):
                if a[i] != b[i]:
                    return a[:i]
            return a[:minLen]
    else:
        newStrings = [common_string(strings[:2], rev = rev)]
        newStrings.extend(strings[2:])
        return common_string(newStrings, rev = rev)


def remove_common_strings(strings, forwards = True, backwards = True):
    """
    remove common section from all strings
    """
    if (not forwards) and (not backwards):
        return strings
    if forwards:
        cStringF = common_string(strings)
        if len(cStringF) > 0:
            strings = [string.replace(cStringF, '', 1) for string in strings]
    if backwards:
        cStringB = common_string(strings, True)
        if len(cStringB) > 0:
            strings = [string[::-1].replace(cStringB[::-1], '', 1)[::-1] for string in strings]
    return strings


def list_cleanup(inList, removeNone = True, unpackTuple = True, unpackList = True, unpackSet = True, unpackDictionary = True, removeDuplicates = True):
    """
    clean up a list, remove None, tuple, nested list set dictionary, or duplicates
    """
    if inList is None:
        return []
    else:
        outList = []
        for item in inList:
            if (removeNone) and (item is None):
                continue
            if (unpackTuple) and isinstance(item, tuple):
                tempList = list_cleanup(list(item), removeNone, unpackTuple, unpackList, unpackSet, unpackDictionary, removeDuplicates)
                outList.extend(tempList)
            elif (unpackList) and isinstance(item, list):
                tempList = list_cleanup(list(item), removeNone, unpackTuple, unpackList, unpackSet, unpackDictionary, removeDuplicates)
                outList.extend(tempList)
            elif (unpackSet) and isinstance(item, set):
                tempList = list_cleanup(list(item), removeNone, unpackTuple, unpackList, unpackSet, unpackDictionary, removeDuplicates)
                outList.extend(tempList)
            elif (unpackDictionary) and isinstance(item, dict):
                tempList = list_cleanup(list(item.values()), removeNone, unpackTuple, unpackList, unpackSet, unpackDictionary, removeDuplicates)
                outList.extend(tempList)
            else:
                outList.append(item)
        if removeDuplicates:
            outList = list(set(outList))
        return outList


def string_to_list(originalStr, convert_raw = False):
    #convert a string of list to a list
    if not convert_raw:
        #remove space after comma
        originalStr = re.sub(r', ',r',', originalStr)
        #remove single and double quotes
        originalStr = re.sub(r'[\'\"]',r'', originalStr)
        #add duoble quotes around items. items defined by separaters including comma
        # no longer support parenthese or square brackets
        originalStr = re.sub(r'([^,]+)',r'"\1"', originalStr)
    #convert to a list
    outlist = ast.literal_eval(originalStr)
    if isinstance(outlist, list) or isinstance(outlist, tuple):
        outlist = [list_cleanup([i]) for i in outlist]
        outlist = [i[0] if len(i) == 1 else tuple(i) for i in outlist]
    else:
        outlist = [outlist]
    #strip spaces
    return outlist


def main():
    print("testing in utilities.py!")
    originalStr = '"a1", "b2", "c3", "d4", "e5", "f6", "g7", "h8", "i9", "j10"'
    print(string_to_list(originalStr))
    originalStr = 'a1, b2, (c3, (d4, e5), [f6, g7]), (h8, i9, j10)'
    print(string_to_list(originalStr))
    originalStr = '(a1, b1), [a1 (abc) cbd, c1, d1]'
    print(string_to_list(originalStr))
    originalStr = '(test) a1, (b1, a1 (abc) cbd, c1), [test d1]'
    print(string_to_list(originalStr))
    originalStr = '("a1",   "b1"), "c1", ["d1", "f1", "g1"]'
    print(string_to_list(originalStr))
    originalStr = '("a1",   "b1"), "c1", [("d1", "f1"), "g1"]'
    print(string_to_list(originalStr, convert_raw = True))
    originalStr = '("a1",   "b1 (test)"), "c1", [("d1", "f1"), "g1"]'
    print(string_to_list(originalStr, convert_raw = True))
    originalStr = '("a1",   "b1 (te\'st)"), "c1", [("d1", "f1"), "g1"]'
    print(string_to_list(originalStr, convert_raw = True))


if __name__ == '__main__' and '__file__' not in globals():
    main()

