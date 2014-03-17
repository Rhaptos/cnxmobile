import os
import urlparse
import Image
from hashlib import md5
from cStringIO import StringIO
from lxml import etree, html
from xml.parsers.expat import ExpatError
from upfront.mathmlimage import convert

def scale(data, w, h, default_format = 'PNG'):
    """ scale image (with material from ImageTag_Hotfix)"""
    #make sure we have valid int's
    size = int(w), int(h)

    original_file=StringIO(data)
    image = Image.open(original_file)
    # consider image mode when scaling
    # source images can be mode '1','L,','P','RGB(A)'
    # convert to greyscale or RGBA before scaling
    # preserve palletted mode (but not pallette)
    # for palletted-only image formats, e.g. GIF
    # PNG compression is OK for RGBA thumbnails
    original_mode = image.mode
    if original_mode == '1':
        image = image.convert('L')
    elif original_mode == 'P':
        image = image.convert('RGBA')
    image.thumbnail(size, Image.ANTIALIAS)
    format = image.format and image.format or default_format
    # decided to only preserve palletted mode
    # for GIF, could also use image.format in ('GIF','PNG')
    if original_mode == 'P' and format == 'GIF':
        image = image.convert('P')
    thumbnail_file = StringIO()
    # quality parameter doesn't affect lossless formats
    image.save(thumbnail_file, format, quality=88)
    thumbnail_file.seek(0)
    return thumbnail_file


def transform(request, response, orig_base, proxied_base, proxied_url, log):
    # force the content_type to text/html otherwise deliverance won't
    # apply rules
    if response.content_type == 'application/xhtml+xml':
        response.content_type = 'text/html'

    if response.content_type in ('image/gif', 'image/png', 'image/jpeg'):
        image_data = response.body
        imgformat = response.content_type.split('/')[-1]
        # temporarily scale image to hardcoded resolution
        scaled_image = scale(image_data, 300, 300, imgformat)
        response.body = scaled_image.read()
        return response

    # we're only interested in html files, not images, css, js, etc.
    if response.content_type != 'text/html':
        return response

    doc = html.fromstring(response.body)

    # search form
    if request.path == '/content/search':

        # transform batch navigation inside table to simple spans
        div = etree.Element("div")
        div.set('id', 'batchnav')
        prevnext = doc.cssselect(
            '#regular_listing > tbody > tr#results_row_two > th > div > span')
        for span in prevnext:
            if span.get('class') in ('previous', 'next'):
                div.append(span)
        if len(prevnext) == 3:
            div.insert(-1, html.fromstring('<span>|</span>'))

        # transform the table of search results to a list
        table = doc.cssselect('#regular_listing')
        if table:
            table = table[0]
            ul = etree.Element("ul")
            ul.set('id', 'results')
            for row in doc.cssselect(
                    '#regular_listing > tbody > tr > td > div.object_name'):
                li = etree.Element("li")
                # get the second anchor around the title of the hit
                a = row.findall('a')[1]
                li.append(a)
                ul.append(li)

            table.getparent().append(div)
            table.getparent().append(ul)
        response.body = etree.tostring(doc)

    # content categories - not the content itself
    elif request.path in ('/content', '/content/'):
        ul = etree.Element("ul")
        ul.set('id', 'cnx_browse')
        for row in doc.cssselect('div#cnx_browse .portletContent ul li'):
            li = etree.Element("li")
            a = row.findall('a')[0]
            li.append(a)
            ul.append(li)

        div = doc.cssselect('div#cnx_browse')[0]
        div.getparent().replace(div, ul)

        response.body = etree.tostring(doc)

    # /content/browse_content/subject
    elif (request.path.startswith('/content/browse_content') and
          len(request.path.split('/')) == 4 ):

        cnx_refine = etree.Element("div")
        cnx_refine.set('id', 'cnx_refine')
        heading = doc.cssselect('#cnx_refine_full h2')[0]
        cnx_refine.append(etree.fromstring(
            '<h1>Browse by %s</h1>' % heading.text_content()))

        ul = etree.Element("ul")
        for row in doc.cssselect('div#cnx_refine .portletContent ul li'):
            li = etree.Element("li")
            a = row.findall('a')[0]
            div = row.findall('div')[0]
            li.append(a)
            li.append(div)
            ul.append(li)
        cnx_refine.append(ul)

        table = doc.cssselect('table#browse_panels')[0]
        table.getparent().replace(table, cnx_refine)
        response.body = etree.tostring(doc)

    # /content/browse_content/subject/Arts
    elif (request.path.startswith('/content/browse_content') and
          len(request.path.split('/')) == 5 ):

        cnx_refine = etree.Element("div")
        cnx_refine.set('id', 'cnx_refine')
        heading = doc.cssselect('#cnx_view_full h2')[0]
        cnx_refine.append(etree.fromstring(
            "<h1>%s</h1>" % heading.text_content()))

        ul = etree.Element("ul")
        for a in doc.cssselect('div#cnx_view table > tr > td > a'):
            li = etree.Element("li")
            href = a.get('href')
            # strip away hostname since some urls are hardcoded to
            # cnx.org
            parts = urlparse.urlparse(href)
            path = parts[2]
            # use the hostname on the request
            parts = urlparse.urlparse(request.url)
            hostname = parts[0] + '://' + parts[1]
            href = hostname + path
            a.set('href', href)
            li.append(a)
            ul.append(li)
        cnx_refine.append(ul)

        table = doc.cssselect('table#browse_panels')[0]
        table.getparent().replace(table, cnx_refine)
        response.body = etree.tostring(doc)

    # modules and collections
    #
    # find all mathml tags and convert them to images
    elif request.path.startswith('/content'):

        # svglib don't handle 'semantics' and 'annotations' tags
        def cleanmathml(element):
            for child in element.getchildren():
                cleanmathml(child)
                # strip namespace attrs - this confuses svglib
                for attr in child.keys():
                    if attr.startswith('xmlns'):
                        del child.attrib[attr]
                if child.tag in ('m:annotation-xml','annotation-xml'):
                    element.remove(child)
                if child.tag in ('m:semantics', 'semantics'):
                    # move the children of semantics tag to parent
                    element.extend(child.getchildren())
                    # remove semantics tag
                    element.remove(child)

        for mathml in doc.cssselect('math'):
            display = mathml.get('display', 'inline')
            cleanmathml(mathml)
            mathmlstring = html.tostring(mathml)

            # lxml has a bug that includes text behind closing tag -
            # manually split it off and it later
            mathmlstring, inlinetext = mathmlstring.split('</math>')
            mathmlstring += '</math>'

            filename = md5(mathmlstring).hexdigest() + '.png'
            filepath = os.path.join(os.getcwd(),
                'theme', 'images', 'mathml', filename)
            if not os.path.exists(filepath):
                try:
                    image_data = convert(mathmlstring)
                    imgfile = open(filepath, 'wb')
                    imgfile.write(image_data)
                    imgfile.close()
                except ExpatError:
                    filename = 'notfound.png'

            img_tag = '<img class="mathml" src="/_theme/images/mathml/%s"/>' % filename 
            if display == 'block':
                img_tag = '<div class="mathml">%s</div>' % img_tag

            if inlinetext:
                img = html.fromstring('%s <span>%s</span>' %(
                    img_tag, inlinetext))
            else:
                img = html.fromstring(img_tag)

            mathml.getparent().replace(mathml, img)

        # find all solutions and display them
        for solution in doc.cssselect('.solution'):
            del solution.attrib['style']

        # delete all solution toggles since we display them all
        for solution_toggle in doc.cssselect('.solution-toggles'):
            solution_toggle.getparent().remove(solution_toggle)

        # replace image with links to image when we render for mxit
        if 'MXit WebBot' in request.headers.get('User-Agent'):
            for img in doc.cssselect('img'):
                anchortag = html.fromstring(
                    '<a href="%s">View Image</a>' % img.attrib['src'])
                img.getparent().replace(img, anchortag)
        else:
            # strip width and height from image tags
            for img in doc.cssselect('img'):
                imgtag = html.fromstring('<img src="%s">' % img.attrib['src'])
                img.getparent().replace(img, imgtag)

        # fix urls in table of contents
        for a in doc.cssselect('div#cnx_course_navigation_contents a'):
            href = a.get('href')
            # strip away hostname since some urls are hardcoded to
            # cnx.org
            parts = urlparse.urlparse(href)
            path = parts[2]
            # use the hostname on the request
            parts = urlparse.urlparse(request.url)
            hostname = parts[0] + '://' + parts[1]
            href = hostname + path
            a.set('href', href)
        
        # Strip style param from ul in table of contents
        for ul in doc.cssselect('div#cnx_course_navigation_contents ul'):
            if 'style' in ul.attrib:
                del ul.attrib['style']
        
        response.body = etree.tostring(doc)

    # lens organizer
    elif request.path.startswith('/lenses') and \
            doc.cssselect('.lensorganizer'):

        div = etree.Element('div')
        for element in doc.cssselect('#region-content > div > div > *'):
            if element.tag == 'h2':
                div.append(element)
            elif element.tag == 'table':
                ul = etree.Element('ul')
                for child in element.iter():
                    if child.tag == 'a':
                        li = etree.Element('li')
                        li.append(child)
                        ul.append(li)
                div.append(ul)

        content_div = doc.cssselect('#region-content > div > div')[0]
        content_div.getparent().replace(content_div, div)

        response.body = etree.tostring(doc)

    # lens results
    elif request.path.startswith('/lenses') and \
            doc.cssselect('.lens_results'):

        div = etree.Element('div')

        heading = doc.cssselect('#region-content h1')[0]
        div.append(heading)

        for path in (
                "//*[@id = 'region-content']/div/p[1]/strong",
                "//*[@id = 'region-content']/div/p[1]/a",
                "//*[@id = 'region-content']/div/p[3]",
                "//*[@class = 'lens_quantity']"):
            for element in doc.xpath(path):
                div.append(element)

        div.append(etree.Element('hr'))

        for selector in (
                "#results_row_two .previous",
                "#results_row_two .next"):
            for element in doc.cssselect(selector):
                div.append(element)

        ul = etree.Element('ul')
        ul.set('id', 'lens_result')
        for row in doc.cssselect('table#regular_listing > tbody > tr > td.object_match'):
            li = etree.Element('li')
            anchors = [e for e in row.iter() if e.tag == 'a']
            li.append(anchors[1])

            object_id = [e for e in row.iter() \
                         if e.get('class') == 'object_id'][0]
            li.append(object_id)

            object_metadata = [e for e in row.iter() \
                               if e.get('class') == 'object_basic_metadata'][0]

            li.append(object_metadata)
            ul.append(li)

        div.append(ul)

        content_div = doc.cssselect('#region-content')[0]
        content_div.getparent().replace(content_div, div)

        response.body = etree.tostring(doc)

    return response


