import pygame
pygame.init()

infoObject = pygame.display.Info()
size = width, height = (infoObject.current_w, infoObject.current_h)
speed = [2, 2]
black = 0, 0, 0

screen = pygame.display.set_mode(size)
DISPLAYSURF = pygame.display.set_mode(size, pygame.FULLSCREEN)

ball = pygame.image.load("intro_ball.gif")
ballrect = ball.get_rect()
clock = pygame.time.Clock()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False  # Set running to False to end the while loop.

    ballrect = ballrect.move(speed)
    if ballrect.left < 0 or ballrect.right > width:
        speed[0] = -speed[0]
    if ballrect.top < 0 or ballrect.bottom > height:
        speed[1] = -speed[1]

    screen.fill(black)
    screen.blit(ball, ballrect)
    pygame.display.flip()
    clock.tick(165)
