import random
import time
import threading
import pygame
import sys
import os
import numpy as np
pr_mode = True
import joblib
mj = joblib.load("./Trafic/model_joblib")
dg = {0: 20, 1: 20, 2: 20, 3: 20}
dr = 120
dy = 2

signals = []
n0light = 4
nowG = 0 
nowY = 0 
# наступний колір світлофора
nextGreen = (
    nowG + 1
) % n0light

speeds = {'car':2, 'bus':1.2, 'truck':1.3, 'bike':2}

# початкові координати транспортних засобів для різних напрямків
x = {'right':[0,0,0], 'down':[620,660,630], 'left':[1400,1400,1400], 'up':[690,730,700]}    
y = {'right':[430,470,440], 'down':[0,0,0], 'left':[360,400,370], 'up':[800,800,800]}

vehicles = {'right': {0:[], 1:[], 2:[], 'crossed':0}, 'down': {0:[], 1:[], 2:[], 'crossed':0}, 'left': {0:[], 1:[], 2:[], 'crossed':0}, 'up': {0:[], 1:[], 2:[], 'crossed':0}}
motor_kind = {0:'car', 1:'bus', 2:'truck', 3:'bike'}
directionNumbers = {0:'right', 1:'down', 2:'left', 3:'up'}


signalCoods = [(530,230),(810,230),(810,570),(530,570)]
signalTimerCoods = [(530,210),(810,210),(810,550),(530,550)]


stopLines = {'right': 590, 'down': 330, 'left': 800, 'up': 535}
defaultStop = {'right': 580, 'down': 320, 'left': 810, 'up': 545}


stop = 25
mov = 25  

ys_motor_kind = {'car': True, 'bus': True, 'truck': True, 'bike': True}
list = []

right = {'right': {1:[], 2:[]}, 'down': {1:[], 2:[]}, 'left': {1:[], 2:[]}, 'up': {1:[], 2:[]}}
left = {'right': {1:[], 2:[]}, 'down': {1:[], 2:[]}, 'left': {1:[], 2:[]}, 'up': {1:[], 2:[]}}

turn = 1.5
# координати середини перехрестя для різних напрямків
mid = {'right': {'x':560, 'y':465}, 'down': {'x':560, 'y':310}, 'left': {'x':860, 'y':310}, 'up': {'x':815, 'y':495}}


# випадкова затримка світлофора
randomG = False
randomRange = [10, 20]

# відображення як довго діє симуляція та координати
elapsed = 0
simulationTime = 0 
coods_time = (1050, 30)


# Параметри для відображення кількості транспортних засобів для різних напрямків та полос
vehicleCountTexts = ["0", "0", "0", "0"]
vehicleCountCoods = [(1050, 70), (1050, 110), (1050, 150), (1050, 190)]

leg1 = 0
leg2 = 0
leg3 = 0
leg4 = 0

tfc = 1 # Параметр для розрахунку часу світлофора
totalflowcoods = (10, 110)
# передбачення вхідних даних
def mtm(on_off, flow1, flow2, flow3, flow4):
    if pr_mode:
        T1_data = np.array(0.44).reshape(-1, 1)
        T1_predict = np.ceil(mj.predict(T1_data))
        if T1_predict < 5:
            T1_predict = 5
        elif T1_predict > 67:
            T1_predict = 67
        print(type(T1_predict))
        print(T1_predict)
        return []
    else:
        return "MODE IS OFF"
L1_percentil = np.array(0.1).reshape(-1, 1)
T1_predict = np.ceil(mj.predict(L1_percentil))
if T1_predict < 5:
    T1_predict = 5
elif T1_predict > 67:
    T1_predict = 67
print(type(T1_predict))
print(T1_predict)
# розрахунок зеленого світла в залежності від потоку транспорту
def rlm(flow):
    f_p = np.array(flow).reshape(-1, 1)
    green_p = np.ceil(mj.predict(f_p))
    return green_p.astype(int)

# розрахунок зеленого часу в залежності від передбачуваного зеленого часу
def mtm(flow):
    f_p = np.array(flow).reshape(-1, 1)
    green_p = np.ceil(mj.predict(f_p))
    if green_p < 2:
        green_p = 1
    elif green_p > 6:
        green_p = 4
    return green_p


# полотно моделі
pygame.init()
simulation = pygame.sprite.Group()

# кольори світлофорів
class TrafficSignal:
    def __init__(self, red, yellow, green):
        self.red = red
        self.yellow = yellow
        self.green = green
        self.signalText = ""


# задання значень і визначення початкової позиції машин
class Vehicle(pygame.sprite.Sprite):
    def __init__(self, lane, vehicleClass, direction_number, direction, will_turn):
        pygame.sprite.Sprite.__init__(self)
        self.lane = lane
        self.vehicleClass = vehicleClass
        self.speed = speeds[vehicleClass]
        self.direction_number = direction_number
        self.direction = direction
        self.x = x[direction][lane]
        self.y = y[direction][lane]
        self.crossed = 0
        self.willTurn = will_turn
        self.turned = 0
        self.rotateAngle = 0
        vehicles[direction][lane].append(self)
        self.index = len(vehicles[direction][lane]) - 1
        self.crossedIndex = 0
        path = "Trafic/images/" + direction + "/" + vehicleClass + ".png"
        self.originalImage = pygame.image.load(path)
        self.image = pygame.image.load(path)
        
# визначення гальмування машини враховуючи положення та розмір попередньої машини   
        if len(vehicles[direction][lane]) > 1 and vehicles[direction][lane][self.index - 1].crossed == 0:
            preceding_vehicle = vehicles[direction][lane][self.index - 1]
    
            if direction in ['right', 'left']:
                width_multiplier = 1 if direction == 'left' else -1
                self.stop = (
                    preceding_vehicle.stop + width_multiplier * preceding_vehicle.image.get_rect().width + width_multiplier * stop
        )
            elif direction in ['down', 'up']:
                height_multiplier = 1 if direction == 'up' else -1
                self.stop = (
                    preceding_vehicle.stop + height_multiplier * preceding_vehicle.image.get_rect().height + height_multiplier * stop
        )
        else:
            self.stop = defaultStop[direction]

# моделювання руху транспортних засобів у візуальному середовищі в залежності від того куди вони повертають         

        if(direction=='right'):
            temp = self.image.get_rect().width + stop    
            x[direction][lane] -= temp
        elif(direction=='left'):
            temp = self.image.get_rect().width + stop
            x[direction][lane] += temp
        elif(direction=='down'):
            temp = self.image.get_rect().height + stop
            y[direction][lane] -= temp
        elif(direction=='up'):
            temp = self.image.get_rect().height + stop
            y[direction][lane] += temp
        simulation.add(self)

    def render(self, screen):
        screen.blit(self.image, (self.x, self.y))

    def move(self):
        if(self.direction=='right'):
            if(self.crossed==0 and self.x+self.image.get_rect().width>stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                if(self.willTurn==0):
                    left[self.direction][self.lane].append(self)
                    self.crossedIndex = len(left[self.direction][self.lane]) - 1
            if(self.willTurn==1):
                if(self.lane == 1):
                    if(self.crossed==0 or self.x+self.image.get_rect().width<stopLines[self.direction]+40):
                        if((self.x+self.image.get_rect().width<=self.stop or (nowG==0 and nowY==0) or self.crossed==1) and (self.index==0 or self.x+self.image.get_rect().width<(vehicles[self.direction][self.lane][self.index-1].x - mov) or vehicles[self.direction][self.lane][self.index-1].turned==1)):               
                            self.x += self.speed
                    else:
                        if(self.turned==0):
                            self.rotateAngle += turn
                            self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                            self.x += 2.4
                            self.y -= 2.8
                            if(self.rotateAngle==90):
                                self.turned = 1
                                right[self.direction][self.lane].append(self)
                                self.crossedIndex = len(right[self.direction][self.lane]) - 1
                        else:
                            if(self.crossedIndex==0 or (self.y>(right[self.direction][self.lane][self.crossedIndex-1].y + right[self.direction][self.lane][self.crossedIndex-1].image.get_rect().height + mov))):
                                self.y -= self.speed
                elif(self.lane == 2):
                    if(self.crossed==0 or self.x+self.image.get_rect().width<mid[self.direction]['x']):
                        if((self.x+self.image.get_rect().width<=self.stop or (nowG==0 and nowY==0) or self.crossed==1) and (self.index==0 or self.x+self.image.get_rect().width<(vehicles[self.direction][self.lane][self.index-1].x - mov) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                 
                            self.x += self.speed
                    else:
                        if(self.turned==0):
                            self.rotateAngle += turn
                            self.image = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                            self.x += 2
                            self.y += 1.8
                            if(self.rotateAngle==90):
                                self.turned = 1
                                right[self.direction][self.lane].append(self)
                                self.crossedIndex = len(right[self.direction][self.lane]) - 1
                        else:
                            if(self.crossedIndex==0 or ((self.y+self.image.get_rect().height)<(right[self.direction][self.lane][self.crossedIndex-1].y - mov))):
                                self.y += self.speed
            else: 
                if(self.crossed == 0):
                    if((self.x+self.image.get_rect().width<=self.stop or (nowG==0 and nowY==0)) and (self.index==0 or self.x+self.image.get_rect().width<(vehicles[self.direction][self.lane][self.index-1].x - mov))):                
                        self.x += self.speed
                else:
                    if((self.crossedIndex==0) or (self.x+self.image.get_rect().width<(left[self.direction][self.lane][self.crossedIndex-1].x - mov))):                 
                        self.x += self.speed
        elif(self.direction=='down'):
            if(self.crossed==0 and self.y+self.image.get_rect().height>stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                if(self.willTurn==0):
                    left[self.direction][self.lane].append(self)
                    self.crossedIndex = len(left[self.direction][self.lane]) - 1
            if(self.willTurn==1):
                if(self.lane == 1):
                    if(self.crossed==0 or self.y+self.image.get_rect().height<stopLines[self.direction]+50):
                        if((self.y+self.image.get_rect().height<=self.stop or (nowG==1 and nowY==0) or self.crossed==1) and (self.index==0 or self.y+self.image.get_rect().height<(vehicles[self.direction][self.lane][self.index-1].y - mov) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                
                            self.y += self.speed
                    else:   
                        if(self.turned==0):
                            self.rotateAngle += turn
                            self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                            self.x += 1.2
                            self.y += 1.8
                            if(self.rotateAngle==90):
                                self.turned = 1
                                right[self.direction][self.lane].append(self)
                                self.crossedIndex = len(right[self.direction][self.lane]) - 1
                        else:
                            if(self.crossedIndex==0 or ((self.x + self.image.get_rect().width) < (right[self.direction][self.lane][self.crossedIndex-1].x - mov))):
                                self.x += self.speed
                elif(self.lane == 2):
                    if(self.crossed==0 or self.y+self.image.get_rect().height<mid[self.direction]['y']):
                        if((self.y+self.image.get_rect().height<=self.stop or (nowG==1 and nowY==0) or self.crossed==1) and (self.index==0 or self.y+self.image.get_rect().height<(vehicles[self.direction][self.lane][self.index-1].y - mov) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                
                            self.y += self.speed
                    else:   
                        if(self.turned==0):
                            self.rotateAngle += turn
                            self.image = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                            self.x -= 2.5
                            self.y += 2
                            if(self.rotateAngle==90):
                                self.turned = 1
                                right[self.direction][self.lane].append(self)
                                self.crossedIndex = len(right[self.direction][self.lane]) - 1
                        else:
                            if(self.crossedIndex==0 or (self.x>(right[self.direction][self.lane][self.crossedIndex-1].x + right[self.direction][self.lane][self.crossedIndex-1].image.get_rect().width + mov))): 
                                self.x -= self.speed
            else: 
                if(self.crossed == 0):
                    if((self.y+self.image.get_rect().height<=self.stop or (nowG==1 and nowY==0)) and (self.index==0 or self.y+self.image.get_rect().height<(vehicles[self.direction][self.lane][self.index-1].y - mov))):                
                        self.y += self.speed
                else:
                    if((self.crossedIndex==0) or (self.y+self.image.get_rect().height<(left[self.direction][self.lane][self.crossedIndex-1].y - mov))):                
                        self.y += self.speed
        elif(self.direction=='left'):
            if(self.crossed==0 and self.x<stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                if(self.willTurn==0):
                    left[self.direction][self.lane].append(self)
                    self.crossedIndex = len(left[self.direction][self.lane]) - 1
            if(self.willTurn==1):
                if(self.lane == 1):
                    if(self.crossed==0 or self.x>stopLines[self.direction]-70):
                        if((self.x>=self.stop or (nowG==2 and nowY==0) or self.crossed==1) and (self.index==0 or self.x>(vehicles[self.direction][self.lane][self.index-1].x + vehicles[self.direction][self.lane][self.index-1].image.get_rect().width + mov) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                
                            self.x -= self.speed
                    else: 
                        if(self.turned==0):
                            self.rotateAngle += turn
                            self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                            self.x -= 1
                            self.y += 1.2
                            if(self.rotateAngle==90):
                                self.turned = 1
                                right[self.direction][self.lane].append(self)
                                self.crossedIndex = len(right[self.direction][self.lane]) - 1
                        else:
                            if(self.crossedIndex==0 or ((self.y + self.image.get_rect().height) <(right[self.direction][self.lane][self.crossedIndex-1].y  -  mov))):
                                self.y += self.speed
                elif(self.lane == 2):
                    if(self.crossed==0 or self.x>mid[self.direction]['x']):
                        if((self.x>=self.stop or (nowG==2 and nowY==0) or self.crossed==1) and (self.index==0 or self.x>(vehicles[self.direction][self.lane][self.index-1].x + vehicles[self.direction][self.lane][self.index-1].image.get_rect().width + mov) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                
                            self.x -= self.speed
                    else:
                        if(self.turned==0):
                            self.rotateAngle += turn
                            self.image = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                            self.x -= 1.8
                            self.y -= 2.5
                            if(self.rotateAngle==90):
                                self.turned = 1
                                right[self.direction][self.lane].append(self)
                                self.crossedIndex = len(right[self.direction][self.lane]) - 1
                        else:
                            if(self.crossedIndex==0 or (self.y>(right[self.direction][self.lane][self.crossedIndex-1].y + right[self.direction][self.lane][self.crossedIndex-1].image.get_rect().height +  mov))):
                                self.y -= self.speed
            else: 
                if(self.crossed == 0):
                    if((self.x>=self.stop or (nowG==2 and nowY==0)) and (self.index==0 or self.x>(vehicles[self.direction][self.lane][self.index-1].x + vehicles[self.direction][self.lane][self.index-1].image.get_rect().width + mov))):                
                        self.x -= self.speed
                else:
                    if((self.crossedIndex==0) or (self.x>(left[self.direction][self.lane][self.crossedIndex-1].x + left[self.direction][self.lane][self.crossedIndex-1].image.get_rect().width + mov))):                
                        self.x -= self.speed
        elif(self.direction=='up'):
            if(self.crossed==0 and self.y<stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                if(self.willTurn==0):
                    left[self.direction][self.lane].append(self)
                    self.crossedIndex = len(left[self.direction][self.lane]) - 1
            if(self.willTurn==1):
                if(self.lane == 1):
                    if(self.crossed==0 or self.y>stopLines[self.direction]-60):
                        if((self.y>=self.stop or (nowG==3 and nowY==0) or self.crossed == 1) and (self.index==0 or self.y>(vehicles[self.direction][self.lane][self.index-1].y + vehicles[self.direction][self.lane][self.index-1].image.get_rect().height +  mov) or vehicles[self.direction][self.lane][self.index-1].turned==1)):
                            self.y -= self.speed
                    else:   
                        if(self.turned==0):
                            self.rotateAngle += turn
                            self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                            self.x -= 2
                            self.y -= 1.2
                            if(self.rotateAngle==90):
                                self.turned = 1
                                right[self.direction][self.lane].append(self)
                                self.crossedIndex = len(right[self.direction][self.lane]) - 1
                        else:
                            if(self.crossedIndex==0 or (self.x>(right[self.direction][self.lane][self.crossedIndex-1].x + right[self.direction][self.lane][self.crossedIndex-1].image.get_rect().width + mov))):
                                self.x -= self.speed
                elif(self.lane == 2):
                    if(self.crossed==0 or self.y>mid[self.direction]['y']):
                        if((self.y>=self.stop or (nowG==3 and nowY==0) or self.crossed == 1) and (self.index==0 or self.y>(vehicles[self.direction][self.lane][self.index-1].y + vehicles[self.direction][self.lane][self.index-1].image.get_rect().height +  mov) or vehicles[self.direction][self.lane][self.index-1].turned==1)):
                            self.y -= self.speed
                    else:   
                        if(self.turned==0):
                            self.rotateAngle += turn
                            self.image = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                            self.x += 1
                            self.y -= 1
                            if(self.rotateAngle==90):
                                self.turned = 1
                                right[self.direction][self.lane].append(self)
                                self.crossedIndex = len(right[self.direction][self.lane]) - 1
                        else:
                            if(self.crossedIndex==0 or (self.x<(right[self.direction][self.lane][self.crossedIndex-1].x - right[self.direction][self.lane][self.crossedIndex-1].image.get_rect().width - mov))):
                                self.x += self.speed
            else: 
                if(self.crossed == 0):
                    if((self.y>=self.stop or (nowG==3 and nowY==0)) and (self.index==0 or self.y>(vehicles[self.direction][self.lane][self.index-1].y + vehicles[self.direction][self.lane][self.index-1].image.get_rect().height + mov))):                
                        self.y -= self.speed
                else:
                    if((self.crossedIndex==0) or (self.y>(left[self.direction][self.lane][self.crossedIndex-1].y + left[self.direction][self.lane][self.crossedIndex-1].image.get_rect().height + mov))):                
                        self.y -= self.speed 
# час зеленого світла
def initialize():
    if pr_mode:
        L1_percen = leg1 / tfc
        L2_percen = leg2 / tfc
        L3_percen = leg3 / tfc
        L4_percen = leg4 / tfc

        T1_predict = mtm(L1_percen)
        T2_predict = mtm(L2_percen)
        T3_predict = mtm(L3_percen)
        T4_predict = mtm(L4_percen)
        ts1 = TrafficSignal(0, dy, T1_predict)
        signals.append(ts1)
        tts1 = ts1.red + ts1.yellow + ts1.green
        ts2 = TrafficSignal(tts1, dy, T2_predict)
        signals.append(ts2)
        tts2 = tts1 + ts2.yellow + ts2.green
        ts3 = TrafficSignal(tts2, dy, T3_predict)
        signals.append(ts3)
        tts3 = tts2 + ts3.yellow + ts3.green
        ts4 = TrafficSignal(tts3, dy, T4_predict)
        signals.append(ts4)
        
    else:
        ts1 = TrafficSignal(0, dy, dg[0])
        signals.append(ts1)
        ts2 = TrafficSignal(ts1.yellow + ts1.green, dy, dg[1])
        signals.append(ts2)
        ts3 = TrafficSignal(dr, dy, dg[2])
        signals.append(ts3)
        ts4 = TrafficSignal(dr, dy, dg[3])
        signals.append(ts4)
    repeat()


def printStatus():
    for i in range(0, 4):
        if signals[i] != None:
            if i == nowG:
                if nowY == 0:
                    print(
                        " GREEN TS",
                        i + 1,
                        "-> r:",
                        signals[i].red,
                        "-> y:",
                        signals[i].yellow,
                        "-> g:",
                        signals[i].green,
                    )
                else:
                    print(
                        "YELLOW TS",
                        i + 1,
                        "-> r:",
                        signals[i].red,
                        "-> y:",
                        signals[i].yellow,
                        "-> g:",
                        signals[i].green,
                    )
            else:
                print(
                    "   RED TS",
                    i + 1,
                    "-> r:",
                    signals[i].red,
                    "-> y:",
                    signals[i].yellow,
                    "-> g:",
                    signals[i].green,
                )
    print()

# світлофор
def repeat():
    global nowG, nowY, nextGreen
    while (
        signals[nowG].green > 0
    ):  
        printStatus()
        updateValues()
        time.sleep(
            1
        )  
    nowY = 1  
    for i in range(0, 3):
        for vehicle in vehicles[directionNumbers[nowG]][i]:
            vehicle.stop = defaultStop[directionNumbers[nowG]]
    while (
        signals[nowG].yellow > 0
    ): 
        printStatus()
        updateValues()
        time.sleep(
            1
        )  
    nowY = 0  

    if pr_mode:
        signals[0].green = mtm(leg1 / tfc)
        signals[1].green = mtm(leg2 / tfc)
        signals[2].green = mtm(leg3 / tfc)
        signals[3].green = mtm(leg4 / tfc)
    else:
        signals[nowG].green = dg[nowG]
    signals[nowG].yellow = dy
    signals[nowG].red = dr

    nowG = nextGreen  
    nextGreen = (nowG + 1) % n0light  
    signals[nextGreen].red = (
        signals[nowG].yellow + signals[nowG].green
    ) 
    repeat()


def updateValues():
    for i in range(0, n0light):
        if i == nowG:
            if nowY == 0:
                signals[i].green -= 1
            else:
                signals[i].yellow -= 1
        else:
            signals[i].red -= 1

# рандомне генерування автомобілів
def generateVehicles():
    global tfc, leg1, leg2, leg3, leg4
    while True:
        vehicle_type = random.choice(list)
        lane_number = random.randint(1, 2)
        will_turn = 0

        if lane_number == 1:
            temp = random.randint(0, 99)
            if temp < 40:
                will_turn = 1
        elif lane_number == 2:
            temp = random.randint(0, 99)
            if temp < 40:
                will_turn = 1

        temp = random.randint(0, 100)

        direction_number = 0
        dist = [5, 11, 56, 101]
        if temp < dist[0]:
            direction_number = 1  #(вниз)
            leg2 += 1
        elif temp < dist[1]:
            direction_number = 3  #(вверх)
            leg4 += 1
        elif temp < dist[2]:
            direction_number = 0  #(право)
            leg1 += 1
        elif temp < dist[3]:
            direction_number = 2  #(ліво)
            leg3 += 1
        Vehicle(
            lane_number,
            motor_kind[vehicle_type],
            direction_number,
            directionNumbers[direction_number],
            will_turn,
        )

        time.sleep(1.25)
        tfc += 1
        print("Total flow count: ", tfc)


# статистика руху
def statistics():
    totalVehicles = 0
    print("Direction-wise Vehicle crossed Counts of Lanes#")
    for i in range(0, 4):
        if signals[i] != None:
            print("Direction", i + 1, ":", vehicles[directionNumbers[i]]["crossed"])
            totalVehicles += vehicles[directionNumbers[i]]["crossed"]
    print("Total vehicles passed: ", totalVehicles)
    print("Total time: ", elapsed)

# розрахування часу симуляції
def simTime():

    global elapsed, simulationTime
    while True:
        elapsed += 1
        time.sleep(1)
        if elapsed == simulationTime:
            statistics()
            os._exit(1)

# запуск
class Main:
    global list
    i = 0
    for vehicleType in ys_motor_kind:
        if ys_motor_kind[vehicleType]:
            list.append(i)
        i += 1
    thread1 = threading.Thread(
        name="initialization", target=initialize, args=()
    )  
    thread1.daemon = True
    thread1.start()

    black = (0, 0, 0)
    white = (255, 255, 255)

    screenWidth = 1400
    screenHeight = 800
    screenSize = (screenWidth, screenHeight)

    background = pygame.image.load("Trafic/images/intersection.png")
    screen = pygame.display.set_mode(screenSize)
    pygame.display.set_caption("SIMULATION")

    redSignal = pygame.image.load("Trafic/images/signals/red.png")
    yellowSignal = pygame.image.load("Trafic/images/signals/yellow.png")
    greenSignal = pygame.image.load("Trafic/images/signals/green.png")
    font = pygame.font.Font(None, 28)
    k = threading.Thread(
        name="generateVehicles1", target=generateVehicles, args=()
    )  
    k.daemon = True
    k.start()
    k2 = threading.Thread(name="simTime", target=simTime, args=())
    k2.daemon = True
    k2.start()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                statistics()
                sys.exit()

        screen.blit(background, (0, 0)) 
        for i in range(
            0, n0light
        ):  
            if i == nowG:
                if nowY == 1:
                    signals[i].signalText = signals[i].yellow
                    screen.blit(yellowSignal, signalCoods[i])
                else:
                    signals[i].signalText = signals[i].green
                    screen.blit(greenSignal, signalCoods[i])
            else:
                signals[i].signalText = signals[i].red
                screen.blit(redSignal, signalCoods[i])
                if signals[i].red <= 200:
                    signals[i].signalText = signals[i].red
                else:
                    signals[i].signalText = "---"
                screen.blit(redSignal, signalCoods[i])
        signalTexts = ["", "", "", ""]

        for i in range(0, n0light):
            signalTexts[i] = font.render(str(signals[i].signalText), True, white, black)
            screen.blit(signalTexts[i], signalTimerCoods[i])

        for vehicle in simulation:
            screen.blit(vehicle.image, [vehicle.x, vehicle.y])
            vehicle.move()
        speed_limit = font.render("Speed limit is 50 km/h", True, black, white)
        car_speed_text = font.render(
            "Current car speed is 41.2 Km/h", True, black, white
        )
        screen.blit(speed_limit, (10, 30))
        screen.blit(car_speed_text, (10, 70))

        for i in range(0, n0light):
            displayText = vehicles[directionNumbers[i]]["crossed"]
            vehicleCountTexts[i] = font.render(
                "Leg#" + str(i + 1) + " Car crossed Count : " + str(displayText),
                True,
                black,
                white,
            )
            screen.blit(vehicleCountTexts[i], vehicleCountCoods[i])

        timeElapsedText = font.render(
            ("Time Elapsed: " + str(elapsed)), True, black, white
        )
        screen.blit(timeElapsedText, coods_time)

        flowcount = font.render(
            "Total flow count: " + str(tfc), True, black, white
        )
        screen.blit(flowcount, totalflowcoods)

        pygame.display.update()



if __name__ == "__main__":
    Main()