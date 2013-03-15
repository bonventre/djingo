from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse

from models import Player, Square, Boardsquare
from forms import NewPlayerForm, NewSquareForm

import random
import simplejson as json

def getscore(player):
  score = 0
  bingo = 0
  for square in Boardsquare.objects.filter(player=player):
    if square.checked:
      score += 1
    if square.order > 25:
      bingo += 1
  if player.bingo:
    bingo += 5
  return score + bingo*1000

def main(request):
  players = Player.objects.all().order_by('-bingo')
  player_info = []
  for player in players:
    score = getscore(player)
    player_info.append({'name':player.name,'id':player.pk,'score':score%1000,'bingo':int(score/5000)})
    player_info = sorted(player_info,key=lambda player: player['bingo']*-5000-player['score']) 

  return render(request, 'bingo/index.html', {'players':player_info})

def playerview(request,playerid):
  player = get_object_or_404(Player,pk=int(playerid))
  score = getscore(player)
  boardsquares = Boardsquare.objects.filter(player=player).order_by('order')
  square_info = []
  bingo_info = []
  for boardsquare in boardsquares:
    if boardsquare.checked:
      classname = 'checked'
    else:
      classname = 'unchecked'
    if boardsquare.order < 25:
      square_info.append({'text':boardsquare.square.text,'boardsquare':boardsquare.pk,'classname':classname})
    else:
      bingo_info.append({'text':boardsquare.square.text,'boardsquare':boardsquare.pk,'classname':classname})
  return render(request, 'bingo/player.html', {'player': player,'score': score%1000,'bingo':int(score/5000),'squares': square_info,'bingosquares':bingo_info})

def newplayer(request):
  success = 0
  playerid = 0
  playername = ''
  if request.method == 'POST':
    form = NewPlayerForm(request.POST)
    if form.is_valid():
      cd = form.cleaned_data
      player = Player(name=cd['name'],bingo=False)
      player.save()
      totalsquares = Square.objects.count()
      if totalsquares >= 25:
        squarei = random.sample(range(2,totalsquares+1),24)
      else:
        squarei = []
        if totalsquares > 1:
          for i in range(24):
            squarei.append(random.randint(2,totalsquares))
        else:
          for i in range(24):
            squarei.append(1)
      squares = Square.objects.all().order_by('pk')
      for i in range(25):
        if i == 12:
          spot = Boardsquare(player=player,square=Square.objects.get(pk=1),checked=True,order=i)
        else:
          if i > 12:
            spot = Boardsquare(player=player,square=squares[squarei[i-1]-1],checked=False,order=i)
          else:
            spot = Boardsquare(player=player,square=squares[squarei[i]-1],checked=False,order=i)
        spot.save()
      playerid = player.pk
      playername = player.name
      success = 1
  else:
    form = NewPlayerForm()
  return render(request, 'bingo/newplayer.html', {'form': form, 'success': success, 'id': playerid, 'name': playername})

def newsquare(request):
  success = 0
  if request.method == 'POST':
    form = NewSquareForm(request.POST)
    if form.is_valid():
      cd = form.cleaned_data
      square = Square(text=cd['text'])
      square.save()
      success = 1
  else:
    form = NewSquareForm()
  return render(request, 'bingo/newsquare.html', {'form': form, 'success': success})

def allsquares(request):
  squares = Square.objects.filter(pk__gt=1)
  return render(request, 'bingo/squares.html', {'squares': squares})

def togglesquare(request):
  if request.method == "POST" and request.is_ajax:
    boardsquare = Boardsquare.objects.get(pk=request.POST['boardsquare'])
    if boardsquare.checked:
      boardsquare.checked = False
      data = {'checked': 0}
    else:
      boardsquare.checked = True
      data = {'checked': 1}
    boardsquare.save()
    player = Player.objects.get(pk=boardsquare.player.pk)
    player.checkforbingo()
    player.save()
    score = getscore(player)
    data['bingonum'] = int(score/5000)
    data['bingo'] = player.bingo
    data['score'] = score%1000
    data = json.dumps(data)
    return HttpResponse(data, mimetype='application/json')
  else:
    raise Http404

def cashinbingo(request,playerid):
  player = Player.objects.get(pk=int(playerid))
  if not player.bingo:
    raise Http404
  else:
    checked = []
    squares = Square.objects.all().order_by('pk')
    squareids = []
    boardsquares = Boardsquare.objects.filter(player=player).order_by('order')
    for boardsquare in boardsquares:
      squareids.append(boardsquare.square.pk)
      if boardsquare.checked:
        checked.append(1)
      else:
        checked.append(0)

    squareids = list(set(squareids))
    squareids.sort()
    totalsquares = Square.objects.count()
    lines = []
    for i in range(5):
      lines.append([5*i,5*i+1,5*i+2,5*i+3,5*i+4])
      lines.append([i,5+i,10+i,15+i,20+i])
    lines.append([0,6,12,18,24])
    lines.append([4,8,12,16,20])
    for line in lines:
      if all(checked[i] == 1 for i in line):
        for pos in line:
          order = boardsquares[pos].order
          if (totalsquares-len(squareids)) > 1:
            i = random.randint(0,totalsquares-len(squareids)-2)
            for j in squareids:
              if squares[i] >= j:
                i += 1
          elif (totalsquares-1) > 1:
            i = random.randint(1,totalsquares-2)
          else:
            i = 0
          newsquare = Boardsquare(player=player,square=squares[i],order=order,checked=False)
          squareids.append(squares[i].pk)
          squareids = list(set(squareids))
          squareids.sort()
          boardsquares[pos].order = 100
          boardsquares[pos].save()
          newsquare.save()
        break

    score = getscore(player)
    player.checkforbingo()
    player.save()
    return HttpResponseRedirect(reverse('bingo.views.playerview',args=(playerid,)))

def deletesquare(request,squareid):
    import pdb;pdb.set_trace()
    square = get_object_or_404(Square,pk=squareid)
    squares = Square.objects.all().order_by('pk')
    boardsquares = Boardsquare.objects.filter(square=square)
    # loop over all boardsquares for the square we are deleting
    for boardsquare in boardsquares:
      # if it is part of a bingo already cashed in, just make it free parking
      if boardsquare.order > 25:
        boardsquare.square = squares[0]
      else:
        # get the other boardsquares on the board containing this one
        board = Boardsquare.objects.filter(player=boardsquare.player)
        squarepks = [square.pk]
        for spot in board:
          squarepks.append(spot.square.pk)
        squarepks = list(set(squarepks))
        squarepks.sort()
        totalsquares = Square.objects.count()
        if (totalsquares-len(squarepks)) > 1:
          i = random.randint(0,totalsquares-len(squarepks)-2)
          for j in squarepks:
            if squares[i].pk >= j:
              i += 1
        elif (totalsquares-1) > 1:
          i = random.randint(1,totalsquares-2)
          if squares[i] >= square.pk:
            i += 1
        else:
          i = 0
        boardsquare.square = squares[i]
        boardsquare.checked = False
      boardsquare.save()
      boardsquare.player.checkforbingo()
      boardsquare.player.save()

    square.delete()
    return HttpResponseRedirect(reverse('bingo.views.allsquares'))

def deleteplayer(request,playerid):
  player = get_object_or_404(Player,pk=playerid)
  boardsquares = Boardsquare.objects.filter(player=player)
  for boardsquare in boardsquares:
    boardsquare.delete()
  player.delete()
  return HttpResponse("Player deleted")
