#coding: utf-8

import sys
sys.setrecursionlimit(25000)
#from PIL import ImageGrab

from PIL import Image
from hamming import avhash, hamming, make_regalur_image_histogram, hist_similar
from time import sleep

dx = [0, 1, 0, -1]
dy = [1, 0, -1, 0]

#class CalculationError

class LianLianKanHelper(object):
    def __init__(self):
        self.sign = None
        self.grab_screen()

    def get_pixel(self, x, y):
        return self.seq[y * self.width + x]
        #return self.im.getpixel((x,y))

    def grab_screen(self):
        #self.im = ImageGrab.grab()
        self.im = Image.open('screenshot.png')
        self.seq = self.im.getdata()
        self.width, self.height = self.im.size

    def find_game_region(self):
        """
        def dfs(x, y):
            if not (0 <= x and x < self.width and 0 <= y and y < self.height):
                return 0
            if self.sign[x][y] == 1:
                return 0
            if self.sign[x][y] == 0 and sum(self.get_pixel(x, y)) == 0:
                self.sign[x][y] = 1
                ret = 0
                for l in range(4):
                    new_x = x + dx[l]
                    new_y = y + dy[l]
                    ret += dfs(new_x, new_y)
                return ret + 1
            else:
                return 0
                """

        def bfs(x, y):
            ret = 1
            queue = [(x,y)]
            self.sign[x][y] = 1
            while len(queue) > 0:
                x, y = queue.pop()
                for l in range(4):
                    new_x = x + dx[l]
                    new_y = y + dy[l]
                    if not (0 <= new_x and new_x < self.width and 0 <= new_y and new_y < self.height):
                        continue
                    if self.sign[new_x][new_y] == 1:
                        continue
                    pixel = self.get_pixel(new_x, new_y)
                    if (pixel[0] == 0 and pixel[1] <=25 and pixel[2] <= 40):# or (abs(pixel[0] - pixel[1]) + abs(pixel[0] - pixel[2]) <= 0 and pixel[0] <= 127):
                    #if sum(self.get_pixel(new_x, new_y)) == 0:
                        self.sign[new_x][new_y] = 1
                        ret += 1
                        queue.append((new_x, new_y))
            return ret

        self.sign = [[0 for j in range(self.height)] for i in range(self.width)]
        for i in range(self.width):
            for j in range(self.height):
                pixel = self.get_pixel(i, j)
                if sum(pixel) == 0:
                    black_count = bfs(i, j)
                    if black_count >= self.width * self.height / 20:
                        print black_count, self.width * self.height / 20
                        print i, j
                        location = self.find_reg_location((i, j),
                                lambda x,y:self.sign[x][y] == 1)
                        return location
        raise Exception

    def find_reg_location(self, start_point, valied_func):
        x, y = start_point
        while valied_func(x + 1, y):
            x += 1
        width_point = x
        x, y = start_point
        while valied_func(x, y + 1):
            y += 1
        height_point = y
        for i in range(start_point[0], width_point + 1):
            if not valied_func(i, height_point):
                #print 'except', i, height_point
                raise Exception
        for j in range(start_point[1], height_point + 1):
            if not valied_func(width_point, j):
                #print 'except', width_point, j
                raise Exception
        return (start_point, (width_point, height_point))

    def find_game_block(self, game_region_location):
        """
        location = self.find_reg_location((158, 292),
                lambda x, y:self.sign[x][y] == 0)
        print location
        return
        """
        start_point, end_point = game_region_location
        game_block_list = []
        for i in range(start_point[0], end_point[0] + 1):
            for j in range(start_point[1], end_point[1] + 1):
                if self.sign[i][j] == 0:
                    try:
                        location = self.find_reg_location((i, j),
                                lambda x, y:self.sign[x][y] == 0)
                    except:
                        location = ((0,0),(0,0))
                    width = location[1][0] - location[0][0]
                    height = location[1][1] - location[0][1]
                    if width >= 30 and abs(width - height) <= width / 5:
                        for ii in range(location[0][0], location[1][0] + 1):
                            for jj in range(location[0][1], location[1][1] + 1):
                                self.sign[ii][jj] = 2
                        game_block_list.append(location)
                        print location
        return game_block_list

    def check_block_list(self, game_block_list):
        if not game_block_list:
            return None
        standard_start_point, standard_end_point = game_block_list[0]
        standard_width = standard_end_point[0] - standard_start_point[0]
        standard_height = standard_end_point[1] - standard_start_point[1]

        for block in game_block_list:
            start_point, end_point = block
            width = end_point[0] - start_point[0]
            height = end_point[1] - start_point[1]
            if not (standard_width * 0.9 <= width and width <= standard_width * 1.1 and
                    standard_height * 0.9 <= height and height <= standard_height * 1.1):
                return None
        return True

    def build_bolck_matrix(self, game_block_list):
        standard_start_point, standard_end_point = game_block_list[0]
        # +1 是考虑还有一条黑边框
        standard_width = standard_end_point[0] - standard_start_point[0] + 1
        standard_height = standard_end_point[1] - standard_start_point[1] + 1

        cut_left = self.width
        cut_top = self.height

        for block in game_block_list:
            cut_left = min(cut_left, block[0][0])
            cut_top = min(cut_top, block[0][1])
        block_matrix = [[0 for j in range(12)] for i in range(16)]
        self.image_matrix = [[0 for j in range(12)] for i in range(16)]
        for block in game_block_list:
            start_point, end_point = block
            postion_x = int(float(start_point[0] - cut_left) / standard_width + 0.5) + 1
            postion_y = int(float(start_point[1] - cut_top) / standard_height + 0.5) + 1
            if not block_matrix[postion_x][postion_y] == 0:
                raise Exception
            # 非常给力的优化 切掉图像边上的一个像素的无用边
            self.image_matrix[postion_x][postion_y] = self.im.crop(
                    map(lambda x:x+1, start_point) + 
                    map(lambda x:x-1, end_point)
                    )
            block_matrix[postion_x][postion_y] = avhash(
                    self.image_matrix[postion_x][postion_y]
                    )
            """
            block_matrix[postion_x][postion_y] = make_regalur_image_histogram(
                    self.image_matrix[postion_x][postion_y]
                    )
            """

        same_block_dict = {}
        block_count = 1
        for i, column in enumerate(block_matrix):
            for j, row in enumerate(column):
                if not row:
                    continue

                finded = False
                for key, value in same_block_dict.iteritems():
                    if hamming(row, key) <= 8:
                    #if hist_similar(row, key) >= 0.80:
                        block_matrix[i][j] = value
                        finded = True
                        break
                if not finded:
                    block_matrix[i][j] = block_count
                    same_block_dict[row] = block_count
                    block_count += 1

        return block_matrix

    def build_matrix(self):
        game_region_location = self.find_game_region()
        print game_region_location
        game_block_list = self.find_game_block(game_region_location)
        print len(game_block_list)
        if self.check_block_list(game_block_list):
            print 'here'
            block_matrix = self.build_bolck_matrix(game_block_list)
            print '\n'.join(map(lambda x:str(x), block_matrix))
            return block_matrix
        else:
            raise Exception

    def find_match_path(self, matrix):
        pass

    def show_match_image(self, matrix, path):
        pass

if __name__ == '__main__':
    llkh = LianLianKanHelper()
    #print llkg.get_pixel(158,292)
    block_matrix = llkh.build_matrix()
    llkh.find_match_path(block_matrix)

