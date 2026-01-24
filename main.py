import pygame
import math
import sys
import random as r
import os

# --- 設定 ---
SCREEN_WIDTH, SCREEN_HEIGHT = 600, 800
FPS = 60

# --- クラス定義 ---

class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            image_path = os.path.join(current_dir, "images", "reimu.png")
            img = pygame.image.load(image_path)
            self.image = pygame.transform.scale(img, (64, 64))
        except:
            self.image = pygame.Surface((64, 64)); self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect(center=(300, 150))
        self.move_timer = 0
        self.max_hp = 5000
        self.hp = 5000
        self.last_phase = 0  # 弾消し判定用のフェーズ管理

class Bullet(pygame.sprite.Sprite):
    images = {}

    def __init__(self, x, y, angle, speed, img_file, scale_x, scale_y, xway=1, index=0, interval=15):
        super().__init__()
        
        if img_file not in Bullet.images:
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                image_path = os.path.join(current_dir, "images", img_file)
                img = pygame.image.load(image_path)
                Bullet.images[img_file] = pygame.transform.scale(img, (scale_x, scale_y))
            except:
                Bullet.images[img_file] = pygame.Surface((10, 10))
                Bullet.images[img_file].fill((255, 0, 0))

        if xway is None or xway <= 0:
            final_angle = angle
        else:
            offset_angle = (xway - 1) * interval / 2.0
            final_angle = angle - offset_angle + (index * interval)

        self.image = pygame.transform.rotate(Bullet.images[img_file], -final_angle - 90)
        self.rect = self.image.get_rect(center=(x, y))
        self.pos_x, self.pos_y = float(x), float(y)
        self.angle = math.radians(final_angle)
        self.speed = speed

    def update(self, *args):
        self.pos_x += math.cos(self.angle) * self.speed
        self.pos_y += math.sin(self.angle) * self.speed
        self.rect.center = (self.pos_x, self.pos_y)
        if not (0 <= self.pos_x <= SCREEN_WIDTH and 0 <= self.pos_y <= SCREEN_HEIGHT):
            self.kill()

# 弾を消す際の処理を管理するクラス
class KillEffect:
    @staticmethod
    def clear_bullets(enemy_bullets):
        """現在の画面上の敵弾をすべて消去する"""
        for b in enemy_bullets:
            b.kill()

class Player(pygame.sprite.Sprite):
    def __init__(self, all_sprites, player_shots):
        super().__init__()
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            image_path = os.path.join(current_dir, "images", "marisa.png")
            img = pygame.image.load(image_path)
            self.image = pygame.transform.scale(img, (48, 48))
        except:
            self.image = pygame.Surface((32, 32)); self.image.fill((0, 255, 255))
        self.rect = self.image.get_rect(center=(300, 700))
        self.hit_radius = 3
        self.all_sprites = all_sprites
        self.player_shots = player_shots
        self.shot_cooldown = 0

    def update(self, keys):
        speed = 2 if keys[pygame.K_LSHIFT] else 5
        if keys[pygame.K_LEFT]:  self.rect.x -= speed
        if keys[pygame.K_RIGHT]: self.rect.x += speed
        if keys[pygame.K_UP]:    self.rect.y -= speed
        if keys[pygame.K_DOWN]:  self.rect.y += speed
        self.rect.clamp_ip(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))

        if keys[pygame.K_z] and self.shot_cooldown <= 0:
            from_pos = [(self.rect.centerx - 10, self.rect.top), (self.rect.centerx + 10, self.rect.top)]
            for p in from_pos:
                s = PlayerShot(p[0], p[1])
                self.all_sprites.add(s); self.player_shots.add(s)
            self.shot_cooldown = 5
        if self.shot_cooldown > 0: self.shot_cooldown -= 1

class PlayerShot(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((8, 20), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, (255, 255, 0), (0, 0, 8, 20))
        self.rect = self.image.get_rect(center=(x, y))
    def update(self, *args):
        self.rect.y -= 15
        if self.rect.bottom < 0: self.kill()

# --- メイン ---
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("東方風弾幕シューティング")
    clock = pygame.time.Clock()
    
    all_sprites = pygame.sprite.Group()
    enemy_bullets = pygame.sprite.Group()
    player_shots = pygame.sprite.Group()
    
    player = Player(all_sprites, player_shots)
    enemy = Enemy()
    all_sprites.add(player, enemy)
    
    frame_count = 0

    while True:
        screen.fill((0, 0, 40))
        keys = pygame.key.get_pressed()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

        frame_count += 1
        
        # --- 敵の弾幕パターン & フェーズ切り替え判定 ---
        tracex = player.rect.centerx - enemy.rect.centerx
        tracey = player.rect.centery - enemy.rect.centery
        angle_to_player = math.degrees(math.atan2(tracey, tracex))
        
        current_phase = 0
        if enemy.hp >= 4900: current_phase = 1
        elif 4701 <= enemy.hp < 4900: current_phase = 2
        elif 4351 <= enemy.hp < 4700: current_phase = 3
        elif 4001 <= enemy.hp < 4350: current_phase = 4
        elif 3700 <= enemy.hp < 4000: current_phase = 5
        elif 3000 <= enemy.hp < 3699: current_phase = 6
        elif 2400 <= enemy.hp < 2999: current_phase = 7
        elif 1750 <= enemy.hp < 2399: current_phase = 8
        elif enemy.hp < 1749: current_phase = 9

        # フェーズが変わった瞬間に画面上の弾を消す
        if enemy.last_phase != current_phase:
            KillEffect.clear_bullets(enemy_bullets)
            enemy.last_phase = current_phase

        # 各フェーズの攻撃
        if current_phase == 1:
            tfmove=0
            h_scale_x=20
            h_scale_y=20
            h2=r.randint(5,19)
            hs=r.randint(1,6)
            if frame_count % 20 == 0:
                for i in range(0, 360, h2):
                    b = Bullet(enemy.rect.centerx, enemy.rect.centery, i, hs, "ohuda_blue.png",h_scale_x,h_scale_y)
                    all_sprites.add(b); enemy_bullets.add(b)
            if frame_count % 30 == 0:
                for i in range(0, 360, h2):
                    b = Bullet(enemy.rect.centerx, enemy.rect.centery, i, hs, "ohuda_red.png",h_scale_x,h_scale_y)
                    all_sprites.add(b); enemy_bullets.add(b)
            if frame_count % 40 == 0:
                for i in range(0, 360, h2):
                    b = Bullet(enemy.rect.centerx, enemy.rect.centery, i, 1, "ohuda_navy.png",20,20)
                    all_sprites.add(b); enemy_bullets.add(b)
        
        elif current_phase == 2:
            # スペルカード発動：見た目を変える（例えば青いお札や激しい動き）
            hx=r.randint(0,50)
            hs=1
            zx=r.randint(50,100)
            if frame_count % 40 == 0:
                hs=1
                for i in range(14):
                    b = Bullet(zx*i-300, 20, 90, hs, "fish.png",20,20)
                    all_sprites.add(b); enemy_bullets.add(b)
                for i in range(14):
                    b = Bullet(zx*i-300, 780, 270, hs, "fish.png",30,30)
                    all_sprites.add(b); enemy_bullets.add(b)
            if frame_count % 60 == 0:
                way=3
                hs = 2
                interval=8
                for i in range (3):
                    b=Bullet(enemy.rect.centerx,enemy.rect.centery,angle_to_player,hs,"ohuda_navy.png",20,20,way,i,interval)
                    all_sprites.add(b); enemy_bullets.add(b)
        elif current_phase == 3:
            h2=r.randint(5,19)
            hs=r.randint(1,6)
            if frame_count % 20 == 0:
                for i in range(0, 360, h2):
                    b = Bullet(enemy.rect.centerx, enemy.rect.centery, i, hs, "normal.png",40,40)
                    all_sprites.add(b); enemy_bullets.add(b)

        elif current_phase == 4:
            h_scale_x=20
            h_scale_y=20
            if frame_count % 30 == 0:
                for i in range(0, 360, h2):
                    b = Bullet(enemy.rect.centerx, enemy.rect.centery, i, hs, "ohuda_purple.png",h_scale_x,h_scale_y)
                    all_sprites.add(b); enemy_bullets.add(b)
            if frame_count % 10 == 0:
                h2=r.randint(5,7)
                hs=1
                ha=r.randint(1,45)
                if frame_count % 20 == 0:
                    for i in range(0, 360, h2):
                        b = Bullet(enemy.rect.centerx, enemy.rect.centery, i+ha, hs, "ohuda_red.png",h_scale_x,h_scale_y)
                        all_sprites.add(b); enemy_bullets.add(b)

        elif current_phase == 5:
            h2=r.randint(5,19)
            hs=r.randint(3,8)
            if frame_count % 11 == 0:
                for i in range(0, 360, h2):
                    b = Bullet(enemy.rect.centerx, enemy.rect.centery, i, hs, "ohuda_navy.png",20,20)
                    all_sprites.add(b); enemy_bullets.add(b)
                for i in range(0, 360, h2):
                    b = Bullet(enemy.rect.centerx, enemy.rect.centery, i, hs, "ohuda_purple.png",20,20)
                    all_sprites.add(b); enemy_bullets.add(b)

        elif current_phase == 6:
            h_scale_x=20
            h_scale_y=20
            h1=r.randint(1,2)
            if frame_count % h1 == 0:
                # 渦巻くような連射弾
                h3=r.randint(2,5)
                angle = (frame_count * 4) % 360
                b = Bullet(enemy.rect.centerx, enemy.rect.centery, angle, h3, "ohuda_blue.png",h_scale_x,h_scale_y)
                all_sprites.add(b); enemy_bullets.add(b)
                r.randint(2,5)
                b2 = Bullet(enemy.rect.centerx, enemy.rect.centery, -angle*1.4, h3, "ohuda_red.png",h_scale_x,h_scale_y)
                all_sprites.add(b2); enemy_bullets.add(b2)
                h3=r.randint(1,4)
                b = Bullet(enemy.rect.centerx, enemy.rect.centery, angle*0.7, h3, "ohuda_purple.png",h_scale_x,h_scale_y)
                all_sprites.add(b); enemy_bullets.add(b)
            if frame_count % 1 == 0:
                angle = (frame_count * 4) % 360
                h3=r.randint(1,3)
                b2 = Bullet(enemy.rect.centerx, enemy.rect.centery, angle*0.3+40, h3, "ohuda_navy.png",h_scale_x,h_scale_y)
                all_sprites.add(b2); enemy_bullets.add(b2)

        elif current_phase == 7:
            h_scale_x=40
            h_scale_y=40
            h2=15
            hs=2
            hx=r.randint(6,570)
            hy=r.randint(0,400)

            if frame_count % 19 == 0:
                for i in range(0, 360, h2):
                    b = Bullet(hx, hy, i, hs, "big_blue.png",h_scale_x,h_scale_y)
                    all_sprites.add(b); enemy_bullets.add(b)

        elif current_phase == 8:
            h_scale_x=20
            h_scale_y=20
            h2=15
            hs=2
            hx=r.randint(6,570)
            hy=r.randint(0,400)

            if frame_count % 19 == 0:
                for i in range(0, 360, h2):
                    b = Bullet(hx, hy, i, hs, "ohuda_purple.png",h_scale_x,h_scale_y)
                    all_sprites.add(b); enemy_bullets.add(b)
            if frame_count % 60 == 0:
                way = 9
                interval=15
                for i in range (way):
                    b=Bullet(enemy.rect.centerx,enemy.rect.centery,angle_to_player,2,"ohuda_navy.png",20,20,way,i,interval)
                    all_sprites.add(b); enemy_bullets.add(b)
                if frame_count%30==0:
                    way=8
                    for i in range (way):
                        way=8
                        b=Bullet(enemy.rect.centerx,enemy.rect.centery,angle_to_player,2,"onnmyou_red.png",120,60,way,i,interval)
                        all_sprites.add(b); enemy_bullets.add(b)
                
            if frame_count % 2 == 0:
                cx=15
                cy=0
                cx0=0
                cy0=1
                for i in range(0,360,60):
                    b=Bullet(player.rect.centerx+cx,player.rect.centery+cy,-i,1,"fish.png",20,20)
                    if cx>0:
                        cx=cx-1
                    if cx<0:
                        cx=cx+1
                    if cx==0:
                        if cx0 == 0:
                            cx=cx-1
                            cx0=1
                        elif cx0 == 1:
                            cx=cx+1
                            cx0=0
                    
                    if cy>0:
                        cy=cy-1
                    if cy<0:
                        cy=cy+1
                    if cy==0:
                        if cy0==0:
                            cy=cy-1
                            cy0=1
                        elif cy0==1:
                            cy=cy+1
                            cy0=0
        elif current_phase == 9:
            img=r.randint(1,13)
            imgp=0
            hx=r.randint(enemy.rect.centerx-50,enemy.rect.centerx+50)
            hy=r.randint(enemy.rect.centery-50,enemy.rect.centery+50)
            hex=20
            hey=20
            if img==1:
                imgp="big,png"
                hex=60
                hey=60
            elif img==2:
                imgp="daenn.png"
                hex=20
                hey=40
            elif img==3:
                imgp="fish.png"
                hex=15
                hey=15
            elif img==4:
                imgp="hishigata.png"
                hex=15
                hey=15
            elif img==5:
                imgp="kunai.png"
                hex=15
                hey=15
            elif img==6:
                imgp="leaf.png"
                hex=15
                hey=15
            elif img==7:
                imgp="mini.png"
                hex=7
                hey=7
            elif img==8:
                imgp="normal.png"
                hex=15
                hey=15
            elif img==9:
                imgp="ohuda_blue.png"
                hex=20
                hey=20
            elif img==10:
                imgp="ohuda_navy.png"
                hex=20
                hey=20
            elif img==11:
                imgp="ohuda_purple.png"
                hex=20
                hey=20
            elif img==12:
                imgp="ohuda_red.png"
                hex=20
                hey=20
            elif img==13:
                imgp="onnmyou_red.png"
                hex=20
                hey=20
            else:
                imgp ="onnmyou_red.png"
                hex=20
                hey=20
            if frame_count % 10==0:
                for i in range(0, 360, 6):
                    b = Bullet(hx, hx, i, 5, imgp,hex,hey)
                    all_sprites.add(b); enemy_bullets.add(b)
                for i in range(0,360,6):
                    b=Bullet(hx+5,hy+5,i,5,imgp,hex,hey)
                    all_sprites.add(b);enemy_bullets.add(b)

        all_sprites.update(keys)

        # 当たり判定
        px, py = player.rect.center
        for b in enemy_bullets:
            if math.hypot(px - b.rect.centerx, py - b.rect.centery) < player.hit_radius + 4:
                pygame.quit(); sys.exit()

        hits = pygame.sprite.spritecollide(enemy, player_shots, True)
        for hit in hits:
            enemy.hp -= 1

        # 描画
        all_sprites.draw(screen)
        
        # HPゲージ
        pygame.draw.rect(screen, (255, 0, 0), (50, 20, 500, 10))
        pygame.draw.rect(screen, (0, 255, 0), (50, 20, max(0, 500 * (enemy.hp / enemy.max_hp)), 10))

        if keys[pygame.K_LSHIFT]:
            pygame.draw.circle(screen, (255, 255, 255), player.rect.center, player.hit_radius)

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()





