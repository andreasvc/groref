<?xml version="1.0" encoding="ISO-8859-1"?>

<xsl:stylesheet version="1.0"  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    
  <xsl:template match="/">

<html>
<head>
  <title>Knack Coreference Corpus</title>
</head>

<body bgcolor="#FFFFEC">
  <font face="Arial, Helvetica, sans-serif" size="5" color="#0000AA">	
  <p align="center">	
  <u>Knack Coreference Corpus</u>
  </p>
  </font>

  <xsl:for-each select=".//COREF[@REF and not (@REF=//COREF/@ID)]">
    <xsl:text>Dangling REF:</xsl:text>
    <xsl:value-of select='@REF'/>
    <xsl:text> 
</xsl:text>
  </xsl:for-each>

  <xsl:for-each select=".//COREF[@REF]">
    <xsl:value-of select='@ID'/>
    <xsl:text>&#8594;</xsl:text>
    <xsl:variable name="Referent">
      <xsl:value-of select='@REF'/>
    </xsl:variable>
    <xsl:apply-templates select="//COREF[@ID=$Referent]" mode="chain"/>
    <br></br>
  </xsl:for-each>



    <font color="black">	
      <xsl:for-each select="knack">
        <br/>
        <xsl:apply-templates select="child::node()"/>
        <hr/>
      </xsl:for-each>
    </font>
</body>
</html>
</xsl:template>

<xsl:template match='COREF'>
  <b>
   <font size="3">
     <xsl:text>[</xsl:text>
     <xsl:apply-templates select="child::node()"/>
   <xsl:text>]</xsl:text>
   <font color="red" size="-1"><sub><xsl:value-of select='@ID'/></sub></font>
   <font color="blue" size="-1"><sub><xsl:value-of select='@REF'/></sub></font>
   
   </font></b>
</xsl:template>

<xsl:template match='COREF' mode="chain">
  <xsl:value-of select='@ID'/>
  <xsl:if test='@REF'>
    <xsl:variable name="Referent">
      <xsl:value-of select='@REF'/>
    </xsl:variable> 
    <xsl:text>&#8594;</xsl:text>
    <xsl:apply-templates select="//COREF[@ID=$Referent]" mode="chain"/>
  </xsl:if>
</xsl:template>


</xsl:stylesheet> 

