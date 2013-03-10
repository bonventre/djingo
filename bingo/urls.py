from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^$', 'bingo.views.main'),
    url(r'^player/(\d+)/$', 'bingo.views.playerview'),
    url(r'^newplayer/', 'bingo.views.newplayer'),
    url(r'^newsquare/', 'bingo.views.newsquare'),
    url(r'^allsquares/', 'bingo.views.allsquares'),
    url(r'^togglesquare/', 'bingo.views.togglesquare'),
)
