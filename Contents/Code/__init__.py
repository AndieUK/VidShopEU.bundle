# VidShop EU
# Version: 1.0
# Released: 6th July 2014	
# Description: A plex plugin to help find those european titles you just can't find with the US agents/sites.

# URLS
VSEU_BASEURL = 'http://www.vidshop.com'
VSEU_SEARCH_MOVIES = VSEU_BASEURL + '/results/%s'
VSEU_MOVIE_INFO = VSEU_BASEURL + '/dvd/%s'
VSEU_COVER_IMG = VSEU_BASEURL + '/cover_front/%s'

def Start():
  HTTP.CacheTime = 0 #CACHE_1DAY
  HTTP.SetHeader('User-agent', 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.2; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)')

class VSEUAgent(Agent.Movies):
  name = 'VidShop EU'
  languages = [Locale.Language.English]
  accepts_from = ['com.plexapp.agents.localmedia']
  primary_provider = True
  
  def search(self, results, media, lang):
  
    Log('Starting Search ...')
    title = media.name
    Log('searching for : ' + title)
    if media.primary_metadata is not None:
      title = media.primary_metadata.title
 
    query = String.URLEncode(String.StripDiacritics(title.replace('-','')))
    query = query.replace('+','%20') #Just a work around.
		
    Log('QUERY: %s', query)
    for movie in HTML.ElementFromURL(VSEU_SEARCH_MOVIES % query).xpath('//a[contains(@class, "ptitle2")]'):

	  # curName = The text in the 'title' p
      curName = movie.text_content().strip()
      if curName.count(', The'):
        curName = 'The ' + curName.replace(', The','',1)
		
      # curID = the ID portion of the href in 'movie'
      curID = movie.get('href').split('/',5)[4]
      score = 100 - Util.LevenshteinDistance(title.lower(), curName.lower())
      if curName.lower().count(title.lower()):
        results.Append(MetadataSearchResult(id = curID, name = curName, score = 100, lang = lang))
      elif (score >= 95):
        results.Append(MetadataSearchResult(id = curID, name = curName, score = score, lang = lang))
    
    results.Sort('score', descending=True)

  def update(self, metadata, media, lang):
    Log('Starting Update for %s', media.title)
    html = HTML.ElementFromURL(VSEU_MOVIE_INFO % metadata.id)
    #As the larger poster image is on its own page, and the filename has no relationship with the thumbnail
    #image we have to load a second page to grab the poster image.	
    posterhtml = HTML.ElementFromURL(VSEU_COVER_IMG % metadata.id ) 
    metadata.title = media.title
	
    #Set tagline to URL
    metadata.tagline = VSEU_MOVIE_INFO % metadata.id	
	
    # Description.
    Log('Starting Description ...')	
    try:
      metadata.summary = html.xpath('//td/p')[0].text_content().replace('\r\n',' ').strip()
      Log('DESCRIPTION: %s', metadata.summary)
      if len(metadata.summary) > 0:
        metadata.summary = metadata.summary
    except: pass

	# Get Thumb and Poster
    Log('Starting Image ...')
    try:	
      imgsml = html.xpath('//img[@border="0" and contains(@src, "/images/content/")]')[0]
      thumbUrl = VSEU_BASEURL + imgsml.get('src') #Grabs thumb image of dvd page.
      Log('THUMBURL: %s', thumbUrl)
      thumb = HTTP.Request(thumbUrl)
      imglrg = posterhtml.xpath('//img[@border="0" and contains(@src, "/images/content/")]')[0]
      posterUrl =	VSEU_BASEURL + imglrg.get('src')
      #posterUrl = thumbUrl.replace('_m_','_l_')  #VSEU_COVER_IMG + metadata.id /images/content/suns_CV052_l_f.jpg
      Log('POSTERURL: %s', posterUrl)	  
      metadata.posters[posterUrl] = Proxy.Preview(thumb)	
    except: pass	
	
    #Rating
    try:
      Log('Starting Rating ...')
      metadata.content_rating = html.xpath('//tr[contains(td[1], "Rating")]/td[3]')[0].text_content().strip()
    except:	pass

    #Director
    try:
      Log('Starting Directors ...')
      metadata.directors.clear()
      director = html.xpath('//tr[contains(td[1], "Directed by")]/td[3]')[0].text_content().strip()
      metadata.directors.add(director)
    except:	pass
	
	#Released
    try:
      Log('Starting Released ...')
      release_date = html.xpath('//tr[contains(td[1], "Release date")]/td[3]')[0].text_content().strip()
      metadata.originally_available_at = Datetime.ParseDate(release_date).date()
      metadata.year = metadata.originally_available_at.year
    except: pass

    # Genre.
    try:
      metadata.genres.clear()
      genres = html.xpath('//tr[contains(td[1], "Category")]/td[3]/a')
      if len(genres) > 0:
        for genreLink in genres:
          genreName = genreLink.text_content().strip('\n')
          metadata.genres.add(genreName)
    except: pass	
	
    #Studio
    try:
      Log('Starting Studio ...')
      metadata.studio = html.xpath('//tr[contains(td[1], "Studio")]//a[@class="ptitle2"]')[0].text_content().strip()
    except: pass	
	
    #Get Cast
    try:
      Log('Starting Cast ...')	
      htmlcast = html.xpath('//td[.//text()[contains(., "Starring :")]]/a')
      for cast in htmlcast:
        cname = cast.text_content().strip()
        if (len(cname) > 0):
          role = metadata.roles.new()
          role.actor = cname
          Log('Cast: %s', cname)
    except: pass