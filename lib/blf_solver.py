import operator

import numpy

from .logging_settings import get_logger

logger = get_logger(name=__name__, level="DEBUG")


class BLFSolver:
    def __init__(self, items):
        self.items = items

    def blf(self, rects, W, reverse=True):
        self.mask = numpy.full((W, W), False, dtype=bool)
        bl_points = [(0, 0)]
        result = []

        def y_reverse(y, height):
            return W - y - height

        for rect_idx in range(len(rects)):
            rect = rects[rect_idx]
            min_bl = None

            for bl_index in range(len(bl_points)):
                blp = bl_points[bl_index]

                if min_bl is not None:
                    minp = bl_points[min_bl]
                    if blp[1] > minp[1]:
                        continue
                    if blp[1] == minp[1] and blp[0] > minp[0]:
                        continue

                if self.is_feas(W, blp, rect):
                    min_bl = bl_index

            # 矩形を配置できなかったのでやり直し
            if min_bl is None:
                logger.debug("blf: space size too small")
                return None

            # 配置予定の矩形
            bl_cand = bl_points[min_bl]
            cx1 = bl_cand[0]
            cx2 = bl_cand[0] + rect[0]
            cy1 = bl_cand[1]
            cy2 = bl_cand[1] + rect[1]

            # 配置予定の矩形と初期エリアのBL安定点候補を追加
            self.check_and_push(bl_points, cx2, 0)
            self.check_and_push(bl_points, 0, cy2)

            # 配置予定の矩形と、配置済み矩形からBL安定点候補を列挙
            for (x, y, w, h, idx, *arg) in result:
                # 配置済みの矩形
                px1 = x
                px2 = x + w
                py1 = y
                py2 = y + h

                if cx2 <= px1 and cy2 > py2:
                    self.check_and_push(bl_points, cx2, py2)
                if px2 <= cx1 and py2 > cy2:
                    self.check_and_push(bl_points, px2, cy2)
                if cy2 <= py1 and cx2 > px2:
                    self.check_and_push(bl_points, px2, cy2)
                if py2 <= cy1 and px2 > cx2:
                    self.check_and_push(bl_points, cx2, py2)

            # 矩形を配置(配置するBL安定点は削除)
            blp = bl_points.pop(min_bl)
            result.append((blp[0], blp[1], rect[0], rect[1], rect_idx) + rect[2:])

            # マスクを更新
            self.mask[
                blp[1]:blp[1] + rect[1],
                blp[0]:blp[0] + rect[0]
            ] = True

        if reverse:
            for idx in range(len(result)):
                r = result[idx]
                result[idx] = (r[0], y_reverse(r[1], r[3])) + r[2:]

        return result

    def solve(self, W=512):
        items = self.items

        items = sorted(items, key=operator.itemgetter(0), reverse=True)
        items = sorted(items, key=operator.itemgetter(1), reverse=True)

        # テクスチャ面積と矩形の合計面積を比較して小さかったら大きくする

        while True:
            result = self.blf(items, W)
            if result is not None:
                break
            W <<= 1
            logger.debug("blf retry: W={}".format(W))

        return (W, result)

    def is_feas(self, W, candp, rect):
        left = candp[0]
        right = candp[0] + rect[0]
        bottom = candp[1]
        top = candp[1] + rect[1]

        if top > W or right > W:
            return False

        # numpy.any で配置済みのところと衝突していたら True なので返すのは反転
        result = not numpy.any(
            self.mask[
                bottom:top,
                left:right
            ]
        )

        return result

    def check_and_push(self, bl_points, x, y):
        size = self.mask.shape

        if size[0] <= y or size[1] <= x:
            return

        if not self.mask[y, x]:
            bl_points.append((x, y))
