<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    exclude-result-prefixes="xs"    
    version="2.0"
    xpath-default-namespace="http://www.tei-c.org/ns/1.0">
    <xsl:template match="/">
        <html>
            <head><title>test</title></head>
            <body>
                <div><xsl:apply-templates select="/TEI/text/body/div"/></div>
            </body>
        </html>
    </xsl:template>
    <xsl:template match="div">
        <h3><xsl:value-of select="head"/></h3>
        <xsl:apply-templates select="p"/>
    </xsl:template>
</xsl:stylesheet>