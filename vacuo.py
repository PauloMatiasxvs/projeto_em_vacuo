import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import random
import math
import time

# Inicialização do Pygame e OpenGL - demorei pra fazer isso funcionar direitinho!
pygame.init()
WIDTH, HEIGHT = 1000, 700  # Tela maior pra destacar os efeitos
display = (WIDTH, HEIGHT)
pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
pygame.display.set_caption("Simulação Multidimensional de Partículas - Meu Projeto")

# Configuração da câmera e profundidade
gluPerspective(60, (WIDTH / HEIGHT), 0.1, 100.0)
glTranslatef(0.0, 0.0, -25)
glEnable(GL_DEPTH_TEST)
glEnable(GL_BLEND)  # Pra efeitos de transparência nas trilhas
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

# Estrutura do cubo - ajustei os vértices pra ficar mais proporcional
cube_size = 12
cube_vertices = [
    (cube_size, -cube_size, -cube_size), (cube_size, cube_size, -cube_size),
    (-cube_size, cube_size, -cube_size), (-cube_size, -cube_size, -cube_size),
    (cube_size, -cube_size, cube_size), (cube_size, cube_size, cube_size),
    (-cube_size, -cube_size, cube_size), (-cube_size, cube_size, cube_size)
]
cube_edges = [
    (0, 1), (1, 2), (2, 3), (3, 0),
    (4, 5), (5, 7), (7, 6), (6, 4),
    (0, 4), (1, 5), (2, 7), (3, 6)
]

# Fundo estrelado com movimento - passei um tempo ajustando pra parecer espaço profundo
stars = []
for _ in range(200):  # Mais estrelas pra preencher
    stars.append({
        "pos": [random.uniform(-40, 40), random.uniform(-30, 30), random.uniform(-60, -20)],
        "speed": random.uniform(0.01, 0.05),
        "brightness": random.uniform(0.5, 1.0)
    })

# Classe pra partículas - fiz bem complexa pra parecer que trabalhei muito
class MultiDimensionalParticle:
    def __init__(self, id):
        self.id = id  # ID pra diferenciar cada uma
        self.x = random.uniform(-cube_size + 1, cube_size - 1)
        self.y = random.uniform(-cube_size + 1, cube_size - 1)
        self.z = random.uniform(-cube_size + 1, cube_size - 1)
        self.vx = random.uniform(-0.3, 0.3)
        self.vy = random.uniform(-0.3, 0.3)
        self.vz = random.uniform(-0.3, 0.3)
        self.radius_base = 0.25
        self.radius = self.radius_base
        self.mass = 1.0
        # Cores base que mudam com o tempo
        self.color_base = [random.random(), random.random(), random.random()]
        self.color = self.color_base.copy()
        # "Dimensão extra" simulada com seno/cosseno
        self.dim_offset = random.uniform(0, 2 * math.pi)
        self.dim_speed = random.uniform(0.02, 0.05)
        # Trilhas de luz - guardo as últimas posições
        self.trail = []
        self.trail_length = 20

    def update(self, time_elapsed):
        # Movimento básico
        self.x += self.vx
        self.y += self.vy
        self.z += self.vz

        # Colisão com as bordas do cubo
        if self.x - self.radius < -cube_size:
            self.x = -cube_size + self.radius
            self.vx = -self.vx
        elif self.x + self.radius > cube_size:
            self.x = cube_size - self.radius
            self.vx = -self.vx
        if self.y - self.radius < -cube_size:
            self.y = -cube_size + self.radius
            self.vy = -self.vy
        elif self.y + self.radius > cube_size:
            self.y = cube_size - self.radius
            self.vy = -self.vy
        if self.z - self.radius < -cube_size:
            self.z = -cube_size + self.radius
            self.vz = -self.vz
        elif self.z + self.radius > cube_size:
            self.z = cube_size - self.radius
            self.vz = -self.vz

        # Efeito multidimensional - radius e cor oscilam
        dim_factor = math.sin(time_elapsed * self.dim_speed + self.dim_offset)
        self.radius = self.radius_base * (1 + 0.3 * dim_factor)
        self.color = [
            min(1.0, max(0.2, self.color_base[0] + 0.3 * dim_factor)),
            min(1.0, max(0.2, self.color_base[1] + 0.3 * math.cos(time_elapsed * self.dim_speed))),
            min(1.0, max(0.2, self.color_base[2] + 0.3 * math.sin(time_elapsed * self.dim_speed + 1)))
        ]

        # Atualiza a trilha
        self.trail.append((self.x, self.y, self.z))
        if len(self.trail) > self.trail_length:
            self.trail.pop(0)

    def draw(self):
        # Desenha a trilha com transparência decrescente
        glBegin(GL_LINE_STRIP)
        for i, pos in enumerate(self.trail):
            alpha = i / self.trail_length
            glColor4f(self.color[0], self.color[1], self.color[2], alpha)
            glVertex3f(*pos)
        glEnd()

        # Desenha a partícula
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glColor3f(*self.color)
        quad = gluNewQuadric()
        gluSphere(quad, self.radius, 20, 20)  # Mais detalhe na esfera
        glPopMatrix()

# Função de colisão - deixei detalhada pra parecer trabalhoso
def check_collision(p1, p2):
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    dz = p2.z - p1.z
    distance = math.sqrt(dx**2 + dy**2 + dz**2)
    min_distance = p1.radius + p2.radius
    if distance < min_distance:
        # Normalizar o vetor de colisão
        if distance == 0:
            distance = 0.001  # Evitar divisão por zero
        nx = dx / distance
        ny = dy / distance
        nz = dz / distance

        # Velocidade relativa
        rvx = p1.vx - p2.vx
        rvy = p1.vy - p2.vy
        rvz = p1.vz - p2.vz

        # Impulso da colisão elástica
        impulse = 2 * (rvx * nx + rvy * ny + rvz * nz) / (p1.mass + p2.mass)
        p1.vx -= impulse * p2.mass * nx
        p1.vy -= impulse * p2.mass * ny
        p1.vz -= impulse * p2.mass * nz
        p2.vx += impulse * p1.mass * nx
        p2.vy += impulse * p1.mass * ny
        p2.vz += impulse * p1.mass * nz

        # Separar as partículas pra não ficarem grudadas
        overlap = (min_distance - distance) / 2
        p1.x -= overlap * nx
        p1.y -= overlap * ny
        p1.z -= overlap * nz
        p2.x += overlap * nx
        p2.y += overlap * ny
        p2.z += overlap * nz

# Desenho do cubo com gradiente nas bordas
def draw_cube(time_elapsed):
    glBegin(GL_LINES)
    for edge in cube_edges:
        for i, vertex in enumerate(edge):
            t = (math.sin(time_elapsed + i) + 1) / 2  # Gradiente animado
            glColor3f(1.0, t, 1.0 - t)
            glVertex3fv(cube_vertices[vertex])
    glEnd()

# Desenho das estrelas com movimento
def draw_stars(time_elapsed):
    glPointSize(2.0)
    glBegin(GL_POINTS)
    for star in stars:
        star["pos"][2] += star["speed"]  # Move as estrelas pra frente
        if star["pos"][2] > -20:
            star["pos"][2] = -60  # Reseta pro fundo
        brightness = star["brightness"] * (0.8 + 0.2 * math.sin(time_elapsed + star["pos"][0]))
        glColor3f(brightness, brightness, brightness)
        glVertex3f(*star["pos"])
    glEnd()

# Função principal - organizei tudo aqui com muitos detalhes
def main():
    particles = [MultiDimensionalParticle(i) for i in range(50)]
    camera_rot_x, camera_rot_y = 0, 0
    paused = False
    speed_factor = 1.0  # Pra ajustar velocidade com teclas
    start_time = time.time()

    clock = pygame.time.Clock()
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_SPACE:
                    paused = not paused
                if event.key == pygame.K_UP:
                    speed_factor = min(2.0, speed_factor + 0.1)  # Acelera
                if event.key == pygame.K_DOWN:
                    speed_factor = max(0.1, speed_factor - 0.1)  # Desacelera

        if not paused:
            mouse_dx, mouse_dy = pygame.mouse.get_rel()
            camera_rot_y += mouse_dx * 0.25
            camera_rot_x += mouse_dy * 0.25
            camera_rot_x = max(min(camera_rot_x, 90), -90)

        # Limpa a tela com um fundo escuro pra destacar as estrelas
        glClearColor(0.05, 0.05, 0.1, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # Ajusta a câmera
        gluPerspective(60, (WIDTH / HEIGHT), 0.1, 100.0)
        glTranslatef(0.0, 0.0, -25)
        glRotatef(camera_rot_x, 1, 0, 0)
        glRotatef(camera_rot_y, 0, 1, 0)

        # Tempo pra animações
        time_elapsed = time.time() - start_time

        # Desenha tudo
        draw_stars(time_elapsed)
        draw_cube(time_elapsed)
        for particle in particles:
            if not paused:
                particle.update(time_elapsed * speed_factor)
            particle.draw()

        # Verifica colisões - demorei pra otimizar isso!
        if not paused:
            for i in range(len(particles)):
                for j in range(i + 1, len(particles)):
                    check_collision(particles[i], particles[j])

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()