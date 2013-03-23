from django.db import models

class Square(models.Model):
  text = models.CharField(max_length=200)

class Player(models.Model):
  name = models.CharField(max_length=50,unique=True) 
  board = models.ManyToManyField(Square, through='Boardsquare')
  stashed_bingos = models.IntegerField(default=0)

  @property
  def score(self):
    score = self.stashed_bingos*5
    for square in Boardsquare.objects.filter(player=self,order__lt=25):
      if square.checked:
        score += 1
    return score
  
  @property
  def maxscore(self):
    return 25+self.stashed_bingos*5

  @property
  def bingo(self):
    checked = []
    for boardsquare in Boardsquare.objects.filter(player=self).order_by('order'):
      if boardsquare.checked:
        checked.append(1)
      else:
        checked.append(0)
    lines = []
    for i in range(5):
      lines.append([5*i,5*i+1,5*i+2,5*i+3,5*i+4])
      lines.append([i,5+i,10+i,15+i,20+i])
    lines.append([0,6,12,18,24])
    lines.append([4,8,12,16,20])
    bingo = False
    for line in lines:
      if all(checked[i] == 1 for i in line):
        bingo = True
        break
    return bingo

  @property
  def bingos(self):
    if self.bingo:
      return self.stashed_bingos + 1
    else:
      return self.stashed_bingos

 

        

class Boardsquare(models.Model):
  player = models.ForeignKey(Player)
  square = models.ForeignKey(Square)
  order = models.IntegerField()
  checked = models.BooleanField()

