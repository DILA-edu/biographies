#!/usr/bin/env python
#-*- coding:utf-8 -*-

__program_name__    = "Simon's XML tools"
__version__         = "0.1"
__author__          = "Simon Wiles"
__email__           = "simonjwiles@gmail.com"
__copyright__       = "Copyright (c) 2010, Simon Wiles"
__license__         = "GPL http://www.gnu.org/licenses/gpl.txt"
__date__            = "March, 2010"
__comments__        = ("Somewhere to collect useful XML processing functions, "
                       "as a library and as a command-line tool")


import sys
import optparse
import logging
import string
from io import StringIO
from lxml import etree

validators = {
    'xsd': etree.XMLSchema,
    'rng': etree.RelaxNG
}


def detectSchematype(schema):
    if schema[-3:] in validators.keys():
        return schema[-3:]
    return False


def formatTree(el, indent='  ', level=0):
    i = '\n%s' % (level*indent)
    if el.tag == etree.Comment:
        el.getparent().remove(el)
    elif len(el):
        if not el.text or not el.text.strip():
            el.text = '%s%s' % (i, indent)
        for e in el:
            formatTree(e, indent, level + 1)
            if not e.tail or not e.tail.strip():
                e.tail = '%s%s' % (i, indent)
        if not e.tail or not e.tail.strip():
            e.tail = i
    else:
        if level and (not el.tail or not el.tail.strip()):
            el.tail = i
        if el.text and el.text.strip():
            txt = el.text.strip('%s%s' % ('\n', string.whitespace))
            if txt.count('\n'):
                el.text = '%s%s%s%s' % (i, indent, txt.replace('\n', '%s%s' % (i, indent)), i)
            else:
                el.text = txt
        if el.tail and el.tail.strip():
            txt = el.tail.strip('%s%s' % ('\n', string.whitespace))
            if txt.count('\n'):
                el.tail = '%s%s%s%s' % (i, indent, txt.replace('\n', '%s%s' % (i, indent)), i)
            else:
                el.tail = txt


def stripComments(tree):
    for el in tree.iter(tag=etree.Comment):
        el.getparent().remove(el)


def validateXML(tree, name, schema=None, schematype=None):

    if schema is None:
        logging.error('No XML schema specified!')
        return False

    if schematype is None: schematype = detectSchematype(schema)
    if schematype == False:
        logging.error('XML schema-type cannot be determined!')
        return False

    logging.debug('XML Schema: %s (%s)' % (schema, schematype))

    validator = validators[schematype](etree.parse(schema))
    if validator(tree):
        logging.info('The %s tree has passed validation!' % name)
        return True
    else:
        log = validator.error_log
        errstring = '\n\n\t'.join(['%d) %s\n\t    in `%s` at line %d, column %d' %
            ((i+1), log[i].message, log[i].filename, log[i].line, log[i].column) for i in range(0,len(log))])
        logging.warning('The %s tree has failed validation (Errors: %d)!\n\n\t%s' %
            (name, len(log), errstring))
        return False


def stripNamespaces(tree):
    # http://wiki.tei-c.org/index.php/Remove-Namespaces.xsl
    xslt_root = etree.XML('''\
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml" indent="no"/>

<xsl:template match="/|comment()|processing-instruction()">
    <xsl:copy>
      <xsl:apply-templates/>
    </xsl:copy>
</xsl:template>

<xsl:template match="*">
    <xsl:element name="{local-name()}">
      <xsl:apply-templates select="@*|node()"/>
    </xsl:element>
</xsl:template>

<xsl:template match="@*">
    <xsl:attribute name="{local-name()}">
      <xsl:value-of select="."/>
    </xsl:attribute>
</xsl:template>
</xsl:stylesheet>
''')
    transform = etree.XSLT(xslt_root)
    tree = transform(tree)
    return tree

if __name__ == '__main__':

    optp = optparse.OptionParser(
                usage=('usage: %prog [options] command filename\n\n\n'
                     'Commands:\n  validate\tPerform XML validation against a schema'
                     '\n  format\tCleanup and prettify an XML tree (output to STDOUT)\n'),
                version='%s v%s' % (__program_name__, __version__)
    )

    validationOpts = optparse.OptionGroup(optp, 'Validation Options')

    validationOpts.add_option('-s', '--schema',
                        dest='schema',
                        help='schema file to use (REQUIRED)'
                    )

    validationOpts.add_option('-t', '--schema-type',
                        type='choice',
                        dest='schematype',
                        choices=['rng', 'xsd',],
                        default=None,
                        help=('schema format (OPTIONAL - detection based on file extension '
                              'will be attempted if this option is not specified)'),
                        metavar='[rng|xsd]'
                    )

    optp.add_option_group(validationOpts)

    formatOpts = optparse.OptionGroup(optp, 'Format Options')

    formatOpts.add_option('-i', '--indent',
                        dest='indent',
                        default='  ',
                        help='string to indent with (e.g. "\t") [%default]'
                    )

    formatOpts.add_option('-r', '--remove-comments',
                        action='store_true',
                        dest='removeComments',
                        default=False,
                        help='strip out XML comments [%default]'
                    )

    optp.add_option_group(formatOpts)

    opts, args = optp.parse_args()

    if len(args) == 0:
        optp.print_help()
        sys.exit()

    if len(args) == 2:
        iFile = args[1]
    else:
        input = sys.stdin.read()
        if input == '':
            optp.error('No input specified!')
        else:
            iFile = StringIO(input)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s.%(msecs)03d (%(module)s) %(levelname)-8s: %(message)s\n',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    try:
        tree = etree.parse(iFile).getroot()
    except IOError:
        logging.fatal('Error reading %s' % iFile)
        sys.exit(2)
    except Exception as e:
        logging.fatal('Error parsing input XML: %s' % e)
        sys.exit(2)

    if args[0] == 'validate':
        if validateXML(tree, opts.schema, opts.schematype):
            sys.exit(0)
        else:
            sys.exit(1)
    elif args[0] == 'format':
        if opts.removeComments:
            stripComments(tree)
        formatTree(tree, opts.indent)
        print( etree.tostring(tree, pretty_print=True, xml_declaration=False, encoding='utf-8') )
    else:
        optp.error('Command not found: %s' % args[0])
