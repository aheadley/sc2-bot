#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.ids.unit_typeid import UnitTypeId
from sc2.tmpfix import creation_ability_from_unit_id
from sc2.ids.ability_id import AbilityId

from pprint import pprint
import itertools

class WorkerRushBot(sc2.BotAI):
    async def on_step(self, state, iteration):
        if iteration == 0:
            self.main_cc = self.units.structure(UnitTypeId.TERRAN_COMMANDCENTER).first
            # self.main_cc = self.units.structure.first

        if iteration % 60 == 0:
            for worker in self.workers.idle:
                mf = self.state.mineral_field.prefer_close_to(worker).first

                await self.do(worker.gather(mf))

        if len(self.workers) < 15 and self.can_afford(UnitTypeId.TERRAN_SCV) \
                and not self.already_pending(UnitTypeId.TERRAN_SCV):
            await self.do(self.main_cc.train(UnitTypeId.TERRAN_SCV, queue=False))

        for depot in self.units.structure.ready.filter(lambda u: u.type_id == UnitTypeId.TERRAN_SUPPLYDEPOT):
            await self.do(depot(AbilityId.MORPH_SUPPLYDEPOT_LOWER))

        if (float(self.state.common.food_used) / float(self.state.common.food_cap)) > 0.8 \
                and self.state.common.food_cap < 200 \
                and self.can_afford(UnitTypeId.TERRAN_SUPPLYDEPOT):
            if not self.already_pending(UnitTypeId.TERRAN_SUPPLYDEPOT):
                await self.build(UnitTypeId.TERRAN_SUPPLYDEPOT,
                    near=self.units(UnitTypeId.TERRAN_SUPPLYDEPOT).random_or(self.main_cc))
                # await self.do(self.workers.prefer_idle.first.build(
                #     UnitTypeId.TERRAN_SUPPLYDEPOT,
                #     await self.find_placement(UnitTypeId.TERRAN_SUPPLYDEPOT, self.main_cc.position)))

        if self.can_afford(UnitTypeId.TERRAN_BARRACKS) \
                and len(self.units.structure.filter(lambda u: u.type_id == UnitTypeId.TERRAN_BARRACKS)) < 2 \
                or self.minerals > 500:
            if not self.already_pending(UnitTypeId.TERRAN_BARRACKS):
                await self.build(UnitTypeId.TERRAN_BARRACKS,
                    near=self.units(UnitTypeId.TERRAN_BARRACKS).random_or(self.main_cc))
                # await self.do(self.workers.prefer_idle.first.build(
                #     UnitTypeId.TERRAN_BARRACKS,
                #     await self.find_placement(UnitTypeId.TERRAN_SUPPLYDEPOT, self.main_cc.position, max_distance=30)))

        if self.can_afford(UnitTypeId.TERRAN_MARINE):
            bb = self.units.structure.filter(lambda u: u.is_idle and u.is_ready and u.type_id == UnitTypeId.TERRAN_BARRACKS).idle
            for b in bb:
                if not any(o.ability == AbilityId.TRAIN_MARINE for o in b.orders):
                    await self.do(b.train(
                        UnitTypeId.TERRAN_MARINE, queue=False))

        idle_mil = self.units.ready.idle.filter(lambda u: not u.is_structure and u.type_id != UnitTypeId.TERRAN_SCV)
        if len(idle_mil) >= 6:
            for u in idle_mil:
                await self.do(u.attack(self.enemy_start_locations[0]))

        if iteration > 0 and iteration % 240 == 0:
            pprint(self.state.common)
            print(self.workers)
            print(self.units.ready.filter(lambda u: not u.is_structure and u.type_id != UnitTypeId.TERRAN_SCV))
            print(self.units.structure)
            print()

if __name__ == '__main__':
    run_game("/home/sc2/StarCraftII/Maps/Melee/Simple64.SC2Map", [
        Bot(Race.Terran, WorkerRushBot()),
        Computer(Race.Protoss, Difficulty.Easy)
    ], realtime=True)
