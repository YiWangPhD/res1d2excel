#!/usr/bin/env python
# coding: utf-8

# Author: Yi Wang
# common utilites


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


def main():
    print("testing in utilities.py!")
    

if __name__ == '__main__' and '__file__' not in globals():
    main()

