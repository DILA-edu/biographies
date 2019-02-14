declare default element namespace "http://www.tei-c.org/ns/1.0";

<html>
<head>
<title>Person, place, time nexus</title>
<link rel="stylesheet" type="text/css" href="stylesGis.css"></link>
</head>
<body>

<h2>Nexus Points</h2>
<p>The nexus points below state that, according to the referenced text, one or more persons were at a certain place at a certain time.</p>
<ol>
{
for $con in doc('JSZwrapper-JuShiZhuan.xml')//body//linkGrp
let $id := data($con/ancestor::div[1]/@xml:id)
order by $id 
return 
         <li>connection ({$id})
           <ul> 
           { 
           for $link in $con/ptr
           return
           if ($link/@type="person")
           then 
             let $perID := substring-after($link/data(@target), '#')
             let $per := doc('JSZwrapper-JuShiZhuan.xml')//body//persName[@xml:id = $perID]
             return
           <li>{data($perID), "=", data($per)}</li>
            else () 
            }
          
           
           {
           for $link in $con/ptr
           return
           if ($link/@type="place")
           then 
             let $plID := substring-after($link/@target, "#")
             let $pl := doc('JSZwrapper-JuShiZhuan.xml')//body//placeName[@xml:id = $plID]
             return
           <li>{data($plID), "=", data($pl)}</li>
           
           else ()
            }
             
             {
           for $link in $con/ptr
           return
           if ($link/@type="time")
           then 
             let $dateID := substring-after($link/@target, "#")
             let $date := doc('JSZwrapper-JuShiZhuan.xml')//body//date[@xml:id = $dateID]
             let $when := $date/@when
             let $from := $date/@from
             let $to:= $date/@to
             let $notBefore := $date/@notBefore
            let $notAfter:= $date/@notAfter
                    return 
                            if ($date/@when)
                            then <li>{data($date), " AD", data($when)}</li>
                            else if  ($date/@from)
                                    then    <li>{data($date), " AD", data($from), "-", data($to)}</li>
                                    else     <li>{data($date), " between AD", data($notBefore), " and", data($notAfter)}</li>
                   else()   
             }  </ul></li>
           
}</ol>
</body>
</html>
