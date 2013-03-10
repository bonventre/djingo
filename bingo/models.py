from django.db import models

class Square(models.Model):
  text = models.CharField(max_length=200)

class Player(models.Model):
  name = models.CharField(max_length=50,unique=True) 
  bingo = models.BooleanField()
  board = models.ManyToManyField(Square, through='Boardsquare')

  def checkforbingo(self):
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
    self.bingo = bingo
      

class Boardsquare(models.Model):
  player = models.ForeignKey(Player)
  square = models.ForeignKey(Square)
  order = models.IntegerField()
  checked = models.BooleanField()

