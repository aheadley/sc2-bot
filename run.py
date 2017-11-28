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

DISTANCE_BUFFER = 3

class WorkerRushBot(sc2.BotAI):
    @property
    def CCs(self):
        return self.units.structure(UnitTypeId.TERRAN_COMMANDCENTER)

    @property
    def MFs(self):
        return self.state.mineral_field

    def _pick_new_base_loc(self):
        mfs = self.MFs
        for cc in self.CCs:
            mfs -= mfs.closer_than(cc.radius+DISTANCE_BUFFER, cc)
        loc = mfs.closest_to(self.CCs.filter(lambda u: u.tag == self._main_cc_tag).first)
        print(loc, loc.position)
        return loc

    async def on_step(self, state, iteration):
        if iteration == 0:
            self._lock_expansion = False
            self._main_cc_tag = self.CCs.first.tag

        if iteration % 30 == 0:
            # TODO: redistribute overloaded mineral fields
            if len(self.CCs.ready) > 1:
                ol_cc = self.CCs.ready.filter(lambda u: u.assigned_harvesters > u.ideal_harvesters)
                ul_cc = self.CCs.ready - ol_cc

                if ul_cc.exists:
                    for cc in ol_cc:
                        workers = self.workers.closer_than(self.MFs.closest_to(cc).distance_to(cc) + DISTANCE_BUFFER, cc)[:cc.ideal_harvesters-cc.assigned_harvesters]
                        for w in workers:
                            await self.do(w.gather(self.MFs.closest_to(ul_cc.closest_to(w))))

            for worker in self.workers.idle:
                mf = self.state.mineral_field.prefer_close_to(worker).first
                await self.do(worker.gather(mf))

        if (float(sum(self.CCs.ready.attrs('assigned_harvesters'))) / float(sum(self.CCs.ready.attrs('ideal_harvesters')))) > 0.9:
            if self.already_pending(UnitTypeId.TERRAN_COMMANDCENTER):
                self._lock_expansion = False
            else:
                if self.can_afford(UnitTypeId.TERRAN_COMMANDCENTER):
                    await self.build(UnitTypeId.TERRAN_COMMANDCENTER, near=self._pick_new_base_loc(), max_distance=10)
                else:
                    self._lock_expansion = True

        # sum(self.CCs.ready.attrs('ideal_harvesters'))
        if len(self.workers) < sum(self.CCs.ready.attrs('ideal_harvesters')) and self.can_afford(UnitTypeId.TERRAN_SCV) \
                and not self.already_training(UnitTypeId.TERRAN_SCV):
            await self.do(self.CCs.ready.random.train(UnitTypeId.TERRAN_SCV, queue=True))

        for depot in self.units.structure.ready(UnitTypeId.TERRAN_SUPPLYDEPOT):
            await self.do(depot(AbilityId.MORPH_SUPPLYDEPOT_LOWER))

        if (float(self.state.common.food_used) / float(self.state.common.food_cap)) > 0.8 \
                and self.state.common.food_cap < 200 \
                and self.can_afford(UnitTypeId.TERRAN_SUPPLYDEPOT):
            if not self.already_pending(UnitTypeId.TERRAN_SUPPLYDEPOT):
                await self.build(UnitTypeId.TERRAN_SUPPLYDEPOT,
                    near=self.units(UnitTypeId.TERRAN_SUPPLYDEPOT).random_or(self.CCs.ready.random))

        if not self._lock_expansion and self.can_afford(UnitTypeId.TERRAN_BARRACKS) \
                and (len(self.units.structure(UnitTypeId.TERRAN_BARRACKS)) < 2 \
                or self.minerals > 500):
            if not self.already_pending(UnitTypeId.TERRAN_BARRACKS):
                await self.build(UnitTypeId.TERRAN_BARRACKS,
                    near=self.units(UnitTypeId.TERRAN_BARRACKS).random_or(self.CCs.ready.random))

        all_barracks = self.units.structure.idle.ready(UnitTypeId.TERRAN_BARRACKS)
        for barracks in all_barracks:
            if not self.can_afford(UnitTypeId.TERRAN_SUPPLYDEPOT):
                break
            if not any(o.ability.id == AbilityId.TRAIN_MARINE for o in barracks.orders):
                await self.do(barracks.train(
                    UnitTypeId.TERRAN_MARINE, queue=True))

        idle_mil = self.units.ready.idle(UnitTypeId.TERRAN_MARINE)
        if len(idle_mil) >= 6:
            for u in idle_mil:
                await self.do(u.attack(self.enemy_start_locations[0]))

        if iteration > 0 and iteration % 240 == 0:
            print(f"### M:{self.state.common.minerals} / V:{self.state.common.vespene} / F:{self.state.common.food_used}/{self.state.common.food_cap} ###")
            print(f"## workers: {len(self.workers)} army: {self.state.common.army_count}")
            print(f"# cc: {len(self.CCs)}; sd: {len(self.units.structure(UnitTypeId.TERRAN_SUPPLYDEPOT) | self.units.structure(UnitTypeId.TERRAN_SUPPLYDEPOTLOWERED))}; bb: {len(self.units.structure(UnitTypeId.TERRAN_BARRACKS))}")
            print()

if __name__ == '__main__':
    run_game("/home/sc2/StarCraftII/Maps/Melee/Simple64.SC2Map", [
        Bot(Race.Terran, WorkerRushBot()),
        Computer(Race.Protoss, Difficulty.Easy)
    ], realtime=True)
