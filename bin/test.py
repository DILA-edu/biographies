# coding: utf_8_sig
''' 轉出 XML 供 InDesign 匯入
'''
import argparse, collections, os, pickle, re, sys

# main
print(sys.argv)
parser = argparse.ArgumentParser()
parser.add_argument("-z", action="store", dest="zhuang", help="某個傳的id")
parser.add_argument("-j", action="store", type=int, dest="juan", help="只輸出某一卷")
parser.add_argument('--b', dest='juan_begin', type=int, help='起始卷數')
parser.add_argument('-e', dest='juan_end', type=int, help='結束卷數')
args = parser.parse_args()
print(JUAN_BEGIN)
print(juan_end)
