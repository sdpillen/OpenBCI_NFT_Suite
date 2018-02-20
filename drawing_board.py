import pygame
from pygame.locals import KEYDOWN


pygame.display.init()      
disp = pygame.display.Info()
WINDOWWIDTH = disp.current_w - 50   #I like the screen slightly smaller than window size for ease of portability
WINDOWHEIGHT = disp.current_h -100
size = [WINDOWWIDTH,WINDOWHEIGHT]

pygame.init()
BLACK     = (0  ,0  ,0  )
WHITE     = (255,255,255)
YELLOW    = (255,255,0)
ORANGE    = (255,165,0)
RED       = (255,0,0)
BASICFONTSIZE = 20
SCOREFONTSIZE = 40 
LINETHICKNESS = 10
BASICFONT = pygame.font.Font('freesansbold.ttf', BASICFONTSIZE)
SCOREFONT = pygame.font.Font('freesansbold.ttf', SCOREFONTSIZE)




screen = pygame.display.set_mode(size)
background = pygame.Surface(screen.get_size())

resultSurf = SCOREFONT.render('PRESS SPACE TO BEGIN STAGE 1', True, WHITE)
resultRect = resultSurf.get_rect()
resultRect.center = (WINDOWWIDTH/2, WINDOWHEIGHT/2-300)
screen.blit(resultSurf, resultRect)

pygame.draw.circle(screen, ORANGE, [WINDOWWIDTH - 1160, WINDOWHEIGHT-400], 8)
pygame.draw.line(screen, RED, ((WINDOWWIDTH-1160),WINDOWHEIGHT-400),((WINDOWWIDTH-1010),WINDOWHEIGHT-600), int(LINETHICKNESS*.4))

pygame.draw.circle(screen, ORANGE, [WINDOWWIDTH - 1010, WINDOWHEIGHT-600], 8)
pygame.draw.line(screen, RED, ((WINDOWWIDTH-1010),WINDOWHEIGHT-600),((WINDOWWIDTH-860),WINDOWHEIGHT-400), int(LINETHICKNESS*.4))

pygame.draw.circle(screen, ORANGE, [WINDOWWIDTH - 860, WINDOWHEIGHT-400], 8)
pygame.draw.line(screen, RED, ((WINDOWWIDTH-860),WINDOWHEIGHT-400),((WINDOWWIDTH-710),WINDOWHEIGHT-600), int(LINETHICKNESS*.4))

pygame.draw.circle(screen, ORANGE, [WINDOWWIDTH - 710, WINDOWHEIGHT-600], 8)


# 1160
# 1010
# 860
# 710

resultSurf = BASICFONT.render("Trial 1", True, WHITE)
resultRect = resultSurf.get_rect()
resultRect.center = (WINDOWWIDTH-1155, WINDOWHEIGHT-250)
screen.blit(resultSurf, resultRect)
pygame.draw.line(screen, WHITE, ((WINDOWWIDTH-1085),WINDOWHEIGHT-300),((WINDOWWIDTH-1085),WINDOWHEIGHT-700), int(LINETHICKNESS*.2))

resultSurf = BASICFONT.render("Trial 2", True, WHITE)
resultRect = resultSurf.get_rect()
resultRect.center = (WINDOWWIDTH-1005, WINDOWHEIGHT-250)
screen.blit(resultSurf, resultRect)
pygame.draw.line(screen, WHITE, ((WINDOWWIDTH-935 ),WINDOWHEIGHT-300),((WINDOWWIDTH-935 ),WINDOWHEIGHT-700), int(LINETHICKNESS*.2))

resultSurf = BASICFONT.render("Trial 3", True, WHITE)
resultRect = resultSurf.get_rect()
resultRect.center = (WINDOWWIDTH-855, WINDOWHEIGHT-250)
screen.blit(resultSurf, resultRect)
pygame.draw.line(screen, WHITE, ((WINDOWWIDTH-785 ),WINDOWHEIGHT-300),((WINDOWWIDTH-785 ),WINDOWHEIGHT-700), int(LINETHICKNESS*.2))

resultSurf = BASICFONT.render("Trial 4", True, WHITE)
resultRect = resultSurf.get_rect()
resultRect.center = (WINDOWWIDTH-705, WINDOWHEIGHT-250)
screen.blit(resultSurf, resultRect)

latitudes = 8 #This is the number of times to split latitudinally
for i in range(0, latitudes):
    pygame.draw.line(screen, WHITE, ((WINDOWWIDTH-635),WINDOWHEIGHT-300-int(i*400/latitudes)),((WINDOWWIDTH-1235),WINDOWHEIGHT-300-int(i*400/latitudes)), int(LINETHICKNESS*.2))
    
    increment = 5
    resultSurf = BASICFONT.render(str(i*increment), True, WHITE)
    resultRect = resultSurf.get_rect()
    resultRect.center = (WINDOWWIDTH-1265, (WINDOWHEIGHT-298-int(i*400/latitudes)))
    screen.blit(resultSurf, resultRect)
    



pygame.draw.rect(screen, WHITE, ((WINDOWWIDTH-635,WINDOWHEIGHT-300),(-600,-400)), LINETHICKNESS)
# b = pygame.sprite.Sprite() # create sprite
# b.image = pygame.image.load("ball.png").convert() # load ball image
# b.image.convert_alpha()
# b.rect = b.image.get_rect() # use image extent values
# b.rect.topleft = [0, 0] # put the ball in the top left corner
# screen.blit(b.image, b.rect)


pygame.display.update()
while pygame.event.poll().type != KEYDOWN:
    pygame.time.delay(100)