# this is largely inspired and copied from https://github.com/KingFooZQ/Totk-Cooking-Simulator/blob/main/simulator.py
# it was also updated to be accurate following the Cooking discoveries made in the TotK datamining server (https://discord.gg/wsXNa2MGwQ) 08/18/2024

import json
import math
import copy

# used multiple times throughout the script (default recipe, clashing effects in elixir, ...)
FAILURE_RECIPE = {
                    "ResultActorName": "Item_Cook_O_01",
                    "PictureBookNum": 145,
                }

class EmptyMaterialListException(Exception):
    pass

class InvalidMaterialException(Exception):
    pass

class TotKCookSim():

    def __init__(self):

        """Initialization of the class."""

        self._load_data()

    def _load_data(self):
        
        """Loads all relevant data in dicionaries/lists. It's possible to use modded data."""

        # too lazy to make another language :)
        self.area_lang = 'USen'

        # holds cooking system data
        with open('Data/SystemData.json', 'r', encoding = 'UTF-8') as json_file:
            self.system_data = json.loads(json_file.read())

        # holds non-single recipe data
        with open('Data/RecipeData.json', 'r', encoding = 'UTF-8') as json_file:
            self.recipes = json.loads(json_file.read())

        # holds single recipe data
        with open('Data/SingleRecipeData.json', 'r', encoding = 'UTF-8') as json_file:
            self.recipes_single = json.loads(json_file.read())

        # holds cooking book data
        with open('Data/RecipeCardData.json', 'r', encoding = 'UTF-8') as json_file:
            self.recipe_card_table = json.loads(json_file.read())

        # holds material data
        self.material = {}
        with open('Data/MaterialData.json', 'r', encoding = 'UTF-8') as json_file:
            materials = json.loads(json_file.read())
            for item in materials:
                self.material[item['ActorName']] = item
        
        # holds effect data
        self.effect = {}
        with open('Data/EffectData.json', 'r', encoding = "UTF-8") as json_file:
            effects = json.loads(json_file.read())
            for item in effects:
                self.effect[item['EffectType']] = item

        # holds language data
        self._index_material_name = {}
        with open('Data/LanguageData.json', 'r', encoding = 'UTF-8') as json_file:
            self._locale_dict = json.loads(json_file.read())
            self._index_material_name_ = {}
            for key, value in self._locale_dict['Material'].items():
                if key.endswith('_Caption'):
                    continue
                for al in value.values():
                    if not al:
                        continue
                    self._index_material_name[al] = key.replace('_Name', '')

    def cook(self, materials: list):

        """Generates meal data for a given material list."""

        if len(materials) == 0:
            raise EmptyMaterialListException('Material list is empty')
        self._tmp = {}
        self.output = {}
        self._material(materials)
        self._recipe()
        self._effect()
        self._hitpoint_recover()
        self._monster_extract()
        self._critical()
        self._spice()
        self._bonus_and_adjust()
        self._sell_price()
        self._super_success_rate()
        self._special_cases()
        self._finish()
        return self.output

    def _material(self, materials: list):

        """Generates a dictionary of the materials."""

        materials_list = []
        for i in materials:
            if not i in self._index_material_name:
                raise InvalidMaterialException(f'Invalid material: {i}')
            actor_name = self._index_material_name[i]
            materials_list.append(self.material[actor_name])
        self._tmp['Materials'] = materials_list
        return
    
    def _recipe(self):

        """Finds the recipe associated with the list of materials."""

        # default recipe (e.g. failure recipe)
        self._tmp['Recipe'] = FAILURE_RECIPE
        materials_list = self._tmp['Materials']
        materials_name_tag = []

        # generate a set of unique object - cooktag pairs
        for material in materials_list:
            actor_name = material['ActorName']
            cook_tag = material['CookTag']
            if (actor_name, cook_tag) not in materials_name_tag:
                materials_name_tag.append((actor_name, cook_tag))

        # if the size of that set is 1, search in the single recipes
        if len(materials_name_tag) == 1:
            for recipe in self.recipes_single:
                # make a copy to not lose the original
                m_copy = copy.copy(materials_name_tag)
                recipe_str = recipe['Recipe']
                # generate list of OK actors/cooktags
                parts_list = recipe_str.split(' or ')

                all_ok = False
                # or_part is a cooktag or a material
                for or_part in parts_list:
                    material = m_copy[0]
                    # if it matches, then recipe is ok and we return it
                    if or_part == material[0] or or_part == material[1]:
                        self._tmp['Recipe'] = recipe
                        return recipe

        # else, search in normal recipes
        else:
            for recipe in self.recipes:
                # make a copy to not lose the original
                m_copy = copy.copy(materials_name_tag)
                if recipe['ResultActorName'] == self.system_data['FailActorName']:
                    self._tmp['Recipe'] = recipe
                recipe_str = recipe['Recipe']
                # generate list of needed parts
                and_parts = recipe_str.split(' + ')
                parts_list = [i.split(' or ') for i in and_parts]
                # if more and_parts than materials in list, go next recipe (impossible to cook this one)
                if len(parts_list) > len(materials_name_tag):
                    continue

                all_ok = True
                # and_part is one or more or_part(s) and is absolutely required to be fulfilled
                for and_part in parts_list:
                    and_ok = False
                    for or_part in and_part:
                        # or_part is an actor or a cooktag
                        for index in range(len(m_copy)):
                            material = m_copy[index]
                            # if it matches, then the and_part is ok and we move on
                            if or_part == material[0] or or_part == material[1]:
                                m_copy.pop(index)
                                and_ok = True
                                break
                        # if and_ok, no need to check more things in the and_part's or_parts and we move on
                        if and_ok:
                            break
                    # if at the end and_ok is not fulfilled, move on to next recipe
                    if not and_ok:
                        all_ok = False
                        break
                if all_ok:
                    self._tmp['Recipe'] = recipe
                    return recipe
        
        # if a normal recipe isn't found, game checks if one of the materials have a CookSpice cooktag, and if so, also checks in the single recipes
        if 'CookSpice' in [i[1] for i in materials_name_tag]:
            for recipe in self.recipes_single:
                # make a copy to not lose the original
                m_copy = copy.copy(materials_name_tag)
                recipe_str = recipe['Recipe']
                # generate list of OK actors/cooktags
                parts_list = recipe_str.split(' or ')

                all_ok = False
                # or_part is a cooktag or a material
                for or_part in parts_list:
                    material = m_copy[0]
                    # if it matches, then recipe is ok and we return it
                    if or_part == material[0] or or_part == material[1]:
                        self._tmp['Recipe'] = recipe
                        return recipe
            
        # should return the failed meal actor at this point
        return recipe

    def _effect(self):

        """Calculates effect, effect level and effect duration"""

        materials_list = self._tmp['Materials']
        recipe = self._tmp['Recipe']
        # set up flag and values
        set_effect_flag = False
        effect_level = 0
        effect_type = None
        effect_time = 0
        bonus_time = 0
        bonus_yellow_hearts = 0
        bonus_stamina = 0

        for mat in materials_list:
            # CookEnemy Spice happens before Monster Extract and Criticals
            if mat.get('CookTag') == "CookEnemy":
                # each material adds its SpiceBoostEffectiveTime, SpiceBoostMaxHeartLevel, SpiceBoostStaminaLevel if they exist, else 0
                # SpiceBoostMaxHeartLevel and SpiceBoostStaminaLevel are present for no material in the game
                bonus_time += mat.get('SpiceBoostEffectiveTime', 0)
                bonus_yellow_hearts += mat.get('SpiceBoostMaxHeartLevel', 0)
                bonus_stamina += mat.get('SpiceBoostStaminaLevel', 0)

        # cycle through all existing effects        
        for effect in self.effect:
            # get amount of materials in the materials list that have the same effect as the one we're cycling through, if > 0, start
            # doing the effect stuff
            effect_materials_num = len([mat for mat in materials_list if mat.get('CureEffectType', "None") == effect])
            if effect_materials_num > 0:
                # set_effect_flag is there to prevent a meal from having multiple effects, if that happens, its effect variables are reset
                # Elixirs are a special case, they turn into a failed meal if they have multiple effects
                if set_effect_flag:
                    effect_level = 0
                    effect_type = None
                    effect_time = 0
                    if recipe['ResultActorName'] == 'Item_Cook_C_17':
                        recipe = FAILURE_RECIPE
                        self._tmp['Recipe'] = FAILURE_RECIPE
                else:
                    effect_type = effect
                # initialize potency sum
                potency_sum = 0
                # add bonus time from CookEnemy
                effect_time += bonus_time
                # cycle through materials of the list, add 30 sec each time, and if the effect of the material matches, add its potency to sum
                for mat in materials_list:
                    if mat.get('CureEffectType', "None") == effect:
                        potency_sum += mat.get('CureEffectLevel', 0)
                    effect_time += 30
                # add basetime of the effect * amount of materials with this effect
                effect_time += effect_materials_num * self.effect[effect].get('BaseTime', 0)
                # effect level = potency * rate, for a compact view of all potency x level equivalents click link below
                # https://docs.google.com/spreadsheets/d/1I9NZiKmGDmYclYObhAfpnXV4sxLnrC4lYVH67WjeO38/edit?usp=sharing
                effect_level += self.effect[effect].get('Rate', 0) * potency_sum
                # add bonus yellow hearts and stamina (no materials have those properties in tears of the kingdom)
                if effect_type == 'LifeMaxUp':
                    effect_level += bonus_yellow_hearts
                elif effect_type in ['StaminaRecovery', 'ExStaminaMaxUp']:
                    effect_level += bonus_stamina
                # clamp effect level to the max value of the effect
                effect_level = min(effect_level, self.effect[effect].get('MaxLv'))
                set_effect_flag = True
        
        # fairy tonic hardcoded values
        if recipe['ResultActorName'] in [self.system_data['FairyActorName'], self.system_data['FailActorName'], "Item_Cook_O_02"]:
            effect_type = None
            effect_level = 0.0
            effect_time = 0

        # just to make sure
        if effect_type in ['LifeMaxUp', 'StaminaRecover', 'ExStaminaMaxUp', 'LifeRepair']:
            effect_time = 0

        self._tmp['Effect'] = effect_type
        self._tmp['EffectLevel'] = effect_level
        self._tmp['EffectTime'] = effect_time
    
    def _hitpoint_recover(self):

        """Calculates the base amount of health recovery"""

        materials_list = self._tmp['Materials']
        recipe = self._tmp['Recipe']
        # initialize health recovery amount
        hitpoint_recover = 0
        for material in materials_list:
            # each material adds its HitPointRecover value if it exists, 0 otherwise
            hitpoint_recover += material.get('HitPointRecover', 0)
        
        # if failed meal, rate is 1.0 (in vanilla game), else 2.0 (basically, when cooked (correctly) materials grant twice more HP than not cooked)
        if recipe['ResultActorName'] == self.system_data['FailActorName']:
            life_recover_rate = self.system_data['SubtleLifeRecoverRate']
        else:
            life_recover_rate = self.system_data['LifeRecoverRate']

        # multiply rate and amount
        hitpoint_recover = hitpoint_recover * life_recover_rate
        self._tmp['HitPointRecover'] = hitpoint_recover
        return

    def _monster_extract(self):

        """Handles Monster Extract shenanigans (mainly starts storing data for all possibilities)"""

        materials_list = self._tmp['Materials']
        effect = self._tmp['Effect']
        effect_level = self._tmp['EffectLevel']
        effect_time = self._tmp['EffectTime']
        hitpoint_recover = self._tmp['HitPointRecover']

        # initialize all flags
        self._monster_extract_time_flag = False
        self._monster_extract_only_health_up_flag = False
        self._monster_extract_only_health_random_flag = False
        self._monster_extract_health_level_random_flag = False
        self._monster_extract_only_level_flag = False
        self._monster_extract_flag = False

        # monster extract has no effect on failed meal & rock hard food
        if self._tmp['Recipe']['ResultActorName'] in [self.system_data['FailActorName'], "Item_Cook_O_02"]:
            return

        # check for monster extract presence
        for mat in materials_list:
            if mat.get("ActorName") == self.system_data['EnemyExtractActorName']:
                self._monster_extract_flag = True

        if self._monster_extract_flag:
            # initiate monster extract section
            self._tmp['Monster Extract'] = {}
            if effect != None and effect_time > 0:
                # this always happens as long as the meal has an effect with a duration
                # sets a time that's either 1:00, 10:00 or 30:00
                self._monster_extract_time_flag = True
                self._tmp['Monster Extract']['EffectTime'] = [60, 600, 1800]

            # the following part is a simplified version of what the game does to know what to do with effect level and health recovery when
            # a monster extract is present in the materials list

            # the self._tmp['Monster Extract'] dictionary is a way to keep track of all possible ways the meal can be affected by, as to not
            # to touch the true stats of the meal

            if (hitpoint_recover == 0 and effect != None) or effect == 'LifeMaxUp':
                # if the meal is not regenerative but has an effect, or is a hearty meal, effect level is either set to min or gets SSAV added
                # at random (50/50) (SSAV = SuperSuccessAddVolume, a property of each effect)
                self._monster_extract_only_level_flag = True
                self._tmp['Monster Extract']['EffectLevel'] = [self.effect[effect].get('MinLv'), effect_level, effect_level + self.effect[effect].get('SuperSuccessAddVolume')]
            elif (hitpoint_recover == 0 and effect != None):
                # if the meal is not regenerative and has no effect, add SSAV of LifeRecover (e.g. 12) to health recovery
                # unsure if this can happen at any point
                self._monster_extract_only_health_up_flag = True
                self._tmp['Monster Extract']['HitPointRecover'] = hitpoint_recover + self.effect['LifeRecover'].get('SuperSuccessAddVolume')
            elif effect != None:
                # if the meal is regenerative and has an effect (that is not hearty), either effect level is touched (either set to min, either gets
                # SSAV added), either health recovery is set to min (1) or gets SSAV of LifeRecover (3 hearts) to it at random (25/25/25/25)
                self._monster_extract_health_level_random_flag = True
                self._tmp['Monster Extract']['HitPointRecover'] = [1, hitpoint_recover, hitpoint_recover + self.effect['LifeRecover'].get('SuperSuccessAddVolume')]
                self._tmp['Monster Extract']['EffectLevel'] = [self.effect[effect].get('MinLv'), effect_level, effect_level + self.effect[effect].get('SuperSuccessAddVolume')]
            else:
                # if the meal is regenerative with no effect, health recovery is either set to min, either gets +3 hearts
                self._monster_extract_only_health_random_flag = True
                self._tmp['Monster Extract']['HitPointRecover'] = [1, hitpoint_recover, hitpoint_recover + self.effect['LifeRecover'].get('SuperSuccessAddVolume')]

    def _critical(self):

        """Handles Critical meals shenanigans (mainly starts storing data for all possibilities)"""

        effect = self._tmp['Effect']
        effect_level = self._tmp['EffectLevel']
        effect_time = self._tmp['EffectTime']
        hitpoint_recover = self._tmp['HitPointRecover']

        # initializes all flags
        self._critical_only_time_flag = False
        self._critical_only_health_flag = False
        self._critical_health_level_flag = False
        self._critical_health_time_flag = False
        self._critical_health_level_time_flag = False
        self._critical_only_level_flag = False
        self._critical_flag = False

        # criticals have no effect on failed meals and rock hard food
        if self._tmp['Recipe']['ResultActorName'] in [self.system_data['FailActorName'], "Item_Cook_O_02"]:
            return

        # monster extract inhibits criticals
        if not self._monster_extract_flag:
            self._critical_flag = True
            # initialize critical section
            self._tmp['Critical'] = {}

            # the following part is a simplified version of what the game does to know what to do with effect level, time and health recovery when
            # a critical hit happens on a meal

            # if effect level <= 1.0, set the effect level to 1.0. That's the main difference between Monster Extract and Crit in regardes to
            # effect level. with crit, if level is chosen to be leveled up, it will always be >= 2.0 and will always be better than without crit,
            # while for monster extract, it has no guarantee to be >= 2.0 (e.g. can stay at level 1)
            if effect_level <= 1.0:
                effect_level, self._tmp['EffectLevel'] = 1.0, 1.0

            if effect == None:
                # if the meal has no effect, since it has no effect level or time, it can only give a health crit. Health crit adds the SSAV of
                # LifeRecover (as seen above, 12 = 3 hearts) to health recovery. All health criticals behave the same
                self._critical_only_health_flag = True
                self._tmp['Critical']['HitPointRecover'] = [hitpoint_recover, hitpoint_recover + self.effect['LifeRecover'].get('SuperSuccessAddVolume')]
            elif effect == "LifeMaxUp":
                # if the effect of the meal is Extra Hearts, its effect level gets the effect's SSAV added to it (in this case, 4 e.g. 1 yellow heart)
                self._critical_only_level_flag = True
                self._tmp['Critical']['EffectLevel'] = [effect_level, effect_level + self.effect[effect].get('SuperSuccessAddVolume')]
            elif effect in ['StaminaRecover', 'ExStaminaMaxUp']:
                # if the effect of the meal is stamina-related, the game checks whether or not the meal is already maxed out in terms of effect level
                if effect_level >= self.effect[effect].get('MaxLv'):
                    # if it is, the meal gets a health crit
                    self._critical_only_health_flag = True
                    self._tmp['Critical']['HitPointRecover'] = [hitpoint_recover, hitpoint_recover + self.effect['LifeRecover'].get('SuperSuccessAddVolume')]
                else:
                    # if it's not, the meal either gets a health crit, or a level crit (effect's SSAV added to it)
                    self._critical_health_level_flag = True
                    self._tmp['Critical']['HitPointRecover'] = [hitpoint_recover, hitpoint_recover + self.effect['LifeRecover'].get('SuperSuccessAddVolume')]
                    self._tmp['Critical']['EffectLevel'] = [effect_level, effect_level + self.effect[effect].get('SuperSuccessAddVolume')]
            elif effect_level >= self.effect[effect].get('MaxLv'):
                # if the meal is maxed out in terms of effect level, the game checks if it's maxed out in terms of health recovery (e.g. >= 40 hearts)
                # honorable mention to LifeRepair (Gloom Recovery) that can get time crit despite being a non-timed effect because devs forgot to add
                # a special case for it
                if hitpoint_recover >= self.effect['LifeRecover'].get('MaxLv'):
                    # if it is, get a time critical, which adds 300 seconds to the meal effect duration (+5:00)
                    self._critical_only_time_flag = True
                    self._tmp['Critical']['EffectTime'] = [effect_time, effect_time + self.system_data.get('SuperSuccessAddEffectiveTime')]
                else:
                    # if it's not, get either a time critical or a health critical
                    self._critical_health_time_flag = True
                    self._tmp['Critical']['HitPointRecover'] = [hitpoint_recover, hitpoint_recover + self.effect['LifeRecover'].get('SuperSuccessAddVolume')]
                    self._tmp['Critical']['EffectTime'] = [effect_time, effect_time + self.system_data.get('SuperSuccessAddEffectiveTime')]
            elif hitpoint_recover >= self.effect['LifeRecover'].get('MaxLv'):
                # if the meal is maxed out in terms of health, get either a health critical or an effect level critical
                # I have no clue why a health critical can be rolled if health is already maxed out, but whatever
                self._critical_health_level_flag = True
                self._tmp['Critical']['HitPointRecover'] = [hitpoint_recover, hitpoint_recover + self.effect['LifeRecover'].get('SuperSuccessAddVolume')]
                self._tmp['Critical']['EffectLevel'] = [effect_level, effect_level + self.effect[effect].get('SuperSuccessAddVolume')]
            else:
                # if none of the cases above is met, roll between all three criticals
                self._critical_health_level_time_flag = True
                self._tmp['Critical']['HitPointRecover'] = [hitpoint_recover, hitpoint_recover + self.effect['LifeRecover'].get('SuperSuccessAddVolume')]
                self._tmp['Critical']['EffectLevel'] = [effect_level, effect_level + self.effect[effect].get('SuperSuccessAddVolume')]
                self._tmp['Critical']['EffectTime'] = [effect_time, effect_time + self.system_data.get('SuperSuccessAddEffectiveTime')]

    def _spice(self):

        """Adds eventual SpiceBoost to the meal properties"""

        # spice doesn't apply to dubious food or rock hard food
        if self._tmp['Recipe']['ResultActorName'] in [self.system_data['FailActorName'], 'Item_Cook_O_02']:
            return
        
        effect = self._tmp['Effect']
        materials_list = self._tmp['Materials']
        # generate list of unique materials
        materials_set = list({item["ActorName"]: item for item in materials_list}.values())
        effect_level = self._tmp['EffectLevel']
        effect_time = self._tmp['EffectTime']
        hitpoint_recover = self._tmp['HitPointRecover']

        # cycle through materials, spice is applied only once per unique materila
        for material in materials_set:
            # CookEnemy spice has already been dealt with before Crit and Monster Extract, which means any time duration granted by CookEnemy
            # materials would get overriden, should a Monster Extract change the time. The other CookTag materials can still add their time after
            if material.get('CookTag') != "CookEnemy":
                # Health spice
                if self._critical_health_level_flag or self._critical_health_level_time_flag or self._critical_health_time_flag or self._critical_only_health_flag:
                    # Increase Critical possibilities
                    self._tmp['Critical']['HitPointRecover'] = [self._tmp['Critical']['HitPointRecover'][0] + material.get('SpiceBoostHitPointRecover', 0), self._tmp['Critical']['HitPointRecover'][1] + material.get('SpiceBoostHitPointRecover', 0)]
                elif self._monster_extract_health_level_random_flag or self._monster_extract_only_health_random_flag:
                    # Increase monster extract possibilities
                    self._tmp['Monster Extract']['HitPointRecover'] = [self._tmp['Monster Extract']['HitPointRecover'][0] + material.get('SpiceBoostHitPointRecover', 0), self._tmp['Monster Extract']['HitPointRecover'][1] + material.get('SpiceBoostHitPointRecover', 0), self._tmp['Monster Extract']['HitPointRecover'][2] + material.get('SpiceBoostHitPointRecover', 0)]
                # each ingerdient adds its SpiceBoostHitPointRecover to the health, if it exists, else it adds 0
                hitpoint_recover += material.get('SpiceBoostHitPointRecover', 0)

                # Time spice
                if self._critical_only_time_flag or self._critical_health_time_flag or self._critical_health_level_time_flag:
                    # Increase Critical possibilities
                    self._tmp['Critical']['EffectTime'] = [self._tmp['Critical']['EffectTime'][0] + material.get('SpiceBoostEffectiveTime', 0), self._tmp['Critical']['EffectTime'][1] + material.get('SpiceBoostEffectiveTime', 0)]
                elif self._monster_extract_time_flag:
                    # Increase monster extract possibilities
                    self._tmp['Monster Extract']['EffectTime'] = [self._tmp['Monster Extract']['EffectTime'][0] + material.get('SpiceBoostEffectiveTime', 0), self._tmp['Monster Extract']['EffectTime'][1] + material.get('SpiceBoostEffectiveTime', 0), self._tmp['Monster Extract']['EffectTime'][2] + material.get('SpiceBoostEffectiveTime', 0)]
                # each ingerdient adds its SpiceBoostEffectiveTime to the effect duration, if it exists, else it adds 0
                effect_time += material.get('SpiceBoostEffectiveTime', 0)
            
            # if the material has the CookSpice tag, it may or may not add its SpiceBoostMaxHeartLevel or SpiceBoostStaminaLevel to the meal
            # if its effect is Extra Hearts or Stamina Recovery/Extra Stamina. However, no material in the game has an existing and non-zero of any
            # of those two properties, so this section is essentially useless in vanilla totk
            if material.get('CookTag') == "CookSpice":
                # Extra Hearts spice
                if effect == "LifeMaxUp":
                    if self._critical_only_level_flag or self._critical_health_level_flag or self._critical_health_level_time_flag:
                        # Increase Critical possibilities
                        self._tmp['Critical']['EffectLevel'] = [self._tmp['Critical']['EffectLevel'][0] + material.get('SpiceBoostMaxHeartLevel', 0), self._tmp['Critical']['EffectLevel'][1] + material.get('SpiceBoostMaxHeartLevel', 0)]
                    elif self._monster_extract_health_level_random_flag or self._monster_extract_only_level_flag:
                        # Increase Monster extract possibilities
                        self._tmp['Monster Extract']['EffectLevel'] = [self._tmp['Monster Extract']['EffectLevel'][0] + material.get('SpiceBoostMaxHeartLevel', 0), self._tmp['Monster Extract']['EffectLevel'][1] + material.get('SpiceBoostMaxHeartLevel', 0), self._tmp['Monster Extract']['EffectLevel'][2] + material.get('SpiceBoostMaxHeartLevel', 0)]
                    # each CookSpice ingredient adds its SpiceBoostMaxHeartLevel to the effect level, if it exists, else it adds 0
                    effect_level += material.get('SpiceBoostMaxHeartLevel', 0)

                # Stamina spice
                elif effect in ['StaminaRecover', 'ExStaminaMaxUp']:
                    if self._critical_only_level_flag or self._critical_health_level_flag or self._critical_health_level_time_flag:
                        # Increase Critical possibilities
                        self._tmp['Critical']['EffectLevel'] = [self._tmp['Critical']['EffectLevel'][0] + material.get('SpiceBoostStaminaLevel', 0), self._tmp['Critical']['EffectLevel'][1] + material.get('SpiceBoostStaminaLevel', 0)]
                    elif self._monster_extract_health_level_random_flag or self._monster_extract_only_level_flag:
                        # Increase Monster Extract possibilities
                        self._tmp['Monster Extract']['EffectLevel'] = [self._tmp['Monster Extract']['EffectLevel'][0] + material.get('SpiceBoostStaminaLevel', 0), self._tmp['Monster Extract']['EffectLevel'][1] + material.get('SpiceBoostStaminaLevel', 0), self._tmp['Monster Extract']['EffectLevel'][2] + material.get('SpiceBoostStaminaLevel', 0)]
                    # each CookSpice ingredient adds its SpiceBoostStaminaLevel to the effect level, if it exists, else it adds 0
                    effect_level += material.get('SpiceBoostStaminaLevel', 0)

        self._tmp['EffectLevel'] = effect_level
        self._tmp['EffectTime'] = effect_time
        self._tmp['HitPointRecover'] = hitpoint_recover

    def _bonus_and_adjust(self):

        """Handles meal bonuses and final calculations of health, as well as duration and level of the effect (if it exists)"""

        recipe = self._tmp['Recipe']
        effect = self._tmp.get('Effect')

        # Bonus meal time
        if self._monster_extract_time_flag:
            self._tmp['Monster Extract']['EffectTime'] = [min(self._tmp['Monster Extract']['EffectTime'][0] + recipe.get('BonusTime', 0), 1800), min(self._tmp['Monster Extract']['EffectTime'][1] + recipe.get('BonusTime', 0), 1800), min(self._tmp['Monster Extract']['EffectTime'][2] + recipe.get('BonusTime', 0), 1800)]
        elif self._critical_only_time_flag or self._critical_health_time_flag or self._critical_health_level_time_flag:
            self._tmp['Critical']['EffectTime'] = [min(self._tmp['Critical']['EffectTime'][0] + recipe.get('BonusTime', 0), 1800), min(self._tmp['Critical']['EffectTime'][1] + recipe.get('BonusTime', 0), 1800)]
        # adds the meal's BonusTime if it exists, and sets EffectTime to 1800 if it's >= 1800
        self._tmp['EffectTime'] = min(self._tmp['EffectTime'] + recipe.get('BonusTime', 0), 1800)

        # Bonus meal health
        if self._critical_health_level_flag or self._critical_health_level_time_flag or self._critical_health_time_flag or self._critical_only_health_flag:
            self._tmp['Critical']['HitPointRecover'] = [min(120, self._tmp['Critical']['HitPointRecover'][0] + recipe.get('BonusHeart', 0)), min(120, self._tmp['Critical']['HitPointRecover'][1] + recipe.get('BonusHeart', 0))]
            self._tmp['Critical']['HitPointRecover'] = [self.effect['LifeRecover'].get('MaxLv') if self._tmp['Critical']['HitPointRecover'][0] == 120 else self._tmp['Critical']['HitPointRecover'][0], self.effect['LifeRecover'].get('MaxLv') if self._tmp['Critical']['HitPointRecover'][1] == 120 else self._tmp['Critical']['HitPointRecover'][1]]
            if effect == 'LifeMaxUp':
                self._tmp['Critical']['HitPointRecover'] = [self.effect['LifeRecover'].get('MaxLv'), self.effect['LifeRecover'].get('MaxLv')]
            if effect == None:
                self._tmp['Critical']['HitPointRecover'] = [1 if self._tmp['Critical']['HitPointRecover'][0] == 0 else self._tmp['Critical']['HitPointRecover'][0], 1 if self._tmp['Critical']['HitPointRecover'][1] == 0 else self._tmp['Critical']['HitPointRecover'][1]]
        elif self._monster_extract_health_level_random_flag or self._monster_extract_only_health_random_flag:
            self._tmp['Monster Extract']['HitPointRecover'] = [min(120, self._tmp['Monster Extract']['HitPointRecover'][0] + recipe.get('BonusHeart', 0)), min(120, self._tmp['Monster Extract']['HitPointRecover'][1] + recipe.get('BonusHeart', 0)), min(120, self._tmp['Monster Extract']['HitPointRecover'][2] + recipe.get('BonusHeart', 0))]
            self._tmp['Monster Extract']['HitPointRecover'] = [self.effect['LifeRecover'].get('MaxLv') if self._tmp['Monster Extract']['HitPointRecover'][0] == 120 else self._tmp['Monster Extract']['HitPointRecover'][0], self.effect['LifeRecover'].get('MaxLv') if self._tmp['Monster Extract']['HitPointRecover'][1] == 120 else self._tmp['Monster Extract']['HitPointRecover'][1], self.effect['LifeRecover'].get('MaxLv') if self._tmp['Monster Extract']['HitPointRecover'][2] == 120 else self._tmp['Monster Extract']['HitPointRecover'][2]]
            if effect == 'LifeMaxUp':
                self._tmp['Monster Extract']['HitPointRecover'] = [self.effect['LifeRecover'].get('MaxLv'), self.effect['LifeRecover'].get('MaxLv'), self.effect['LifeRecover'].get('MaxLv')]
            if effect == None:
                self._tmp['Monster Extract']['HitPointRecover'] = [1 if self._tmp['Monster Extract']['HitPointRecover'][0] == 0 else self._tmp['Monster Extract']['HitPointRecover'][0], 1 if self._tmp['Monster Extract']['HitPointRecover'][1] == 0 else self._tmp['Monster Extract']['HitPointRecover'][1], 1 if self._tmp['Monster Extract']['HitPointRecover'][2] == 0 else self._tmp['Monster Extract']['HitPointRecover'][2]]
        
        # adds the meal's BonusHeart if it exists, and sets HitPointRecover to 120 if it's >= 120
        self._tmp['HitPointRecover'] = min(120, self._tmp['HitPointRecover'] + recipe.get('BonusHeart', 0))
        # if HitPointRecover is 120, set it to LifeRecover's MaxLv e.g. 160
        self._tmp['HitPointRecover'] = self.effect['LifeRecover'].get('MaxLv') if self._tmp['HitPointRecover'] == 120 else self._tmp['HitPointRecover']
        # if no effect and no health recovery, sets health recovery to 1 (there is no meal with no effect and no health recovery)
        if effect == None:
            self._tmp['HitPointRecover'] = 1 if self._tmp['HitPointRecover'] == 0 else self._tmp['HitPointRecover']

        # Clamping Effect
        if effect:
            if self._monster_extract_only_level_flag or self._monster_extract_health_level_random_flag:
                self._tmp['Monster Extract']['EffectLevel'] = [min(self.effect[effect].get('MaxLv'), self._tmp['Monster Extract']['EffectLevel'][0]), min(self.effect[effect].get('MaxLv'), self._tmp['Monster Extract']['EffectLevel'][1]), min(self.effect[effect].get('MaxLv'), self._tmp['Monster Extract']['EffectLevel'][2])]
                self._tmp['Monster Extract']['EffectLevel'] = [1.0 if self._tmp['Monster Extract']['EffectLevel'][0] <= 1.0 and self._tmp['Monster Extract']['EffectLevel'][0] > 0 else self._tmp['Monster Extract']['EffectLevel'][0], 1.0 if self._tmp['Monster Extract']['EffectLevel'][1] <= 1.0 and self._tmp['Monster Extract']['EffectLevel'][1] > 0 else self._tmp['Monster Extract']['EffectLevel'][1], 1.0 if self._tmp['Monster Extract']['EffectLevel'][2] <= 1.0 and self._tmp['Monster Extract']['EffectLevel'][2] > 0 else self._tmp['Monster Extract']['EffectLevel'][2]]
                if effect in ['LifeMaxUp', 'LifeRepair']:
                    self._tmp['Monster Extract']['EffectLevel'] = [4 * round(self._tmp['Monster Extract']['EffectLevel'][0] / 4), 4 * round(self._tmp['Monster Extract']['EffectLevel'][1] / 4), 4 * round(self._tmp['Monster Extract']['EffectLevel'][2] / 4)]
                    self._tmp['Monster Extract']['EffectLevel'] = [4 if self._tmp['Monster Extract']['EffectLevel'][0] <= 4.0 and self._tmp['Monster Extract']['EffectLevel'][0] > 0 else self._tmp['Monster Extract']['EffectLevel'][0], 4 if self._tmp['Monster Extract']['EffectLevel'][1] <= 4.0 and self._tmp['Monster Extract']['EffectLevel'][1] > 0 else self._tmp['Monster Extract']['EffectLevel'][1], 4 if self._tmp['Monster Extract']['EffectLevel'][2] <= 4.0 and self._tmp['Monster Extract']['EffectLevel'][2] > 0 else self._tmp['Monster Extract']['EffectLevel'][2]]
                self._tmp['Monster Extract']['EffectLevel'] = [math.floor(self._tmp['Monster Extract']['EffectLevel'][0]), math.floor(self._tmp['Monster Extract']['EffectLevel'][1]), math.floor(self._tmp['Monster Extract']['EffectLevel'][2])]
            elif self._critical_health_level_flag or self._critical_health_level_time_flag or self._critical_only_level_flag:
                self._tmp['Critical']['EffectLevel'] = [min(self.effect[effect].get('MaxLv'), self._tmp['Critical']['EffectLevel'][0]), min(self.effect[effect].get('MaxLv'), self._tmp['Critical']['EffectLevel'][1])]
                self._tmp['Critical']['EffectLevel'] = [1.0 if self._tmp['Critical']['EffectLevel'][0] <= 1.0 and self._tmp['Critical']['EffectLevel'][0] > 0 else self._tmp['Critical']['EffectLevel'][0], 1.0 if self._tmp['Critical']['EffectLevel'][1] <= 1.0 and self._tmp['Critical']['EffectLevel'][1] > 0 else self._tmp['Critical']['EffectLevel'][1]]
                if effect in ['LifeMaxUp', 'LifeRepair']:
                    self._tmp['Critical']['EffectLevel'] = [4 * round(self._tmp['Critical']['EffectLevel'][0] / 4), 4 * round(self._tmp['Critical']['EffectLevel'][1] / 4)]
                    self._tmp['Critical']['EffectLevel'] = [4 if self._tmp['Critical']['EffectLevel'][0] <= 4.0 and self._tmp['Critical']['EffectLevel'][0] > 0 else self._tmp['Critical']['EffectLevel'][0], 4 if self._tmp['Critical']['EffectLevel'][1] <= 4.0 and self._tmp['Critical']['EffectLevel'][1] > 0 else self._tmp['Critical']['EffectLevel'][1]]
                self._tmp['Critical']['EffectLevel'] = [math.floor(self._tmp['Critical']['EffectLevel'][0]), math.floor(self._tmp['Critical']['EffectLevel'][1])]
            
            # Sets EffectLevel to its MaxLv if EffectLevel >= MaxLv
            self._tmp['EffectLevel'] = min(self.effect[effect].get('MaxLv'), self._tmp['EffectLevel'])
            # Sets EffectLevel to 1.0 if EffectLevel between 0 (not included) and 1
            self._tmp['EffectLevel'] = 1.0 if self._tmp['EffectLevel'] <= 1.0 and self._tmp['EffectLevel'] > 0 else self._tmp['EffectLevel']
            # Rounds to the nearest 4 so that only whole hearts are allowed for Extra Hearts and Gloom Recovery
            if effect in ['LifeMaxUp', 'LifeRepair']:
                self._tmp['EffectLevel'] = 4 * round(self._tmp['EffectLevel'] / 4)
                self._tmp['EffectLevel'] = 4 if self._tmp['EffectLevel'] <= 4.0 and self._tmp['EffectLevel'] > 0 else self._tmp['EffectLevel']
            # Final effect level is floored
            self._tmp['EffectLevel'] = math.floor(self._tmp['EffectLevel'])

    def _sell_price(self):

        """Calculates the sell price of the meal."""

        # initialize sell price
        selling_price = 0
        materials_list = self._tmp['Materials']

        # cycle through all materials, if they have CookLowPrice add 1, else add their sell price
        for material in materials_list:
            if material.get('CookLowPrice', False):
                selling_price += 1
            else:
                selling_price += material.get('SellingPrice', 0)

        # multiply by the sell rate (defined by amount of materials) and round down
        for item in self.system_data['PriceRateList']:
            if item['MaterialNum'] == len(materials_list):
                self._tmp['SellingPrice'] = math.floor(selling_price * item['Rate'])
            # can't be lower than 2, unless fairy tonic, rock hard meal or dubious food

        self._tmp['SellingPrice'] = max(self._tmp['SellingPrice'], 3)
        if self._tmp['Recipe']['ResultActorName'] in ['Item_Cook_O_02', self.system_data['SubtleLifeRecover'], self.system_data['FairyActorName']]:
            self._tmp['SellingPrice'] = 2

        return

    def _super_success_rate(self):

        """Calculates the chances of critical hit"""

        materials_set = set()
        self._tmp['SuperSuccessRate'] = 0
        materials_list = self._tmp['Materials']

        # cycle through all materials in the list
        for material in materials_list:
            # take max of SpiceBoostSuccessRate
            self._tmp['SuperSuccessRate'] = max(self._tmp['SuperSuccessRate'], material.get('SpiceBoostSuccessRate', 0))
            # also calculating amount of unique materials
            materials_set.add(material['ActorName'])
        
        # add max of SpiceBoostSuccessRate and the Rate defined by unique material amount
        for item in self.system_data['SuperSuccessRateList']:
            if item['MaterialTypeNum'] == len(materials_set):
                self._tmp['SuperSuccessRate'] += item['Rate']
                return

    def _special_cases(self):

        """Ensures default properties for failed meals"""

        # dubious food restores 1 heart, rock hard food restores 1/4 heart, both have no effect
        recipe = self._tmp['Recipe']
        if recipe['ResultActorName'] in ['Item_Cook_O_02', self.system_data['SubtleLifeRecover']]:
            if recipe['ResultActorName'] == "Item_Cook_O_02":
                self._tmp['HitPointRecover'] = self.system_data['FailLifeRecover']
            else:
                self._tmp['HitPointRecover'] = self.system_data['SubtleLifeRecover']
            self._tmp['Effect'] = None
            self._tmp['EffectTime'] = 0
            self._tmp['EffectLevel'] = 0

    def _finish(self):

        """Handles formatting the data for output"""

        self._tmp['RNG'] = ''
        result_actor_name = self._tmp['Recipe']['ResultActorName']
        effect = self._tmp.get('Effect')
        
        # gets base meal name
        locale_actor_name = self._locale_dict['Meal'][f'{result_actor_name}_Name'][self.area_lang]
        
        locale_effect_name = ''
        locale_buff_name = ''

        if effect:
            # gets effect prefix
            locale_effect_name = self._locale_dict['Effect'][effect+'_Name'][self.area_lang]
            # gets effect name
            locale_buff_name = self._locale_dict['Buff'][effect][self.area_lang]
            # full meal name
            locale_meal_name = locale_effect_name + ' ' + locale_actor_name
        else:
            locale_meal_name = locale_actor_name
        if not locale_buff_name:
            locale_buff_name = "None"

        # effect time formatting

        # gets crit time "+3:00" string
        crit_time_min, crit_time_sec = divmod(self.system_data['SuperSuccessAddEffectiveTime'], 60)
        crit_time_string = "{:02d}:{:02d}".format(int(crit_time_min), int(crit_time_sec))

        if self._monster_extract_time_flag:
            # if monster extract affects time, generate string for all three times
            minutes0, seconds0 = divmod(self._tmp['Monster Extract']['EffectTime'][0], 60)
            minutes1, seconds1 = divmod(self._tmp['Monster Extract']['EffectTime'][1], 60)
            minutes2, seconds2 = divmod(self._tmp['Monster Extract']['EffectTime'][2], 60)
            effect_time_str0 = "{:02d}:{:02d}".format(int(minutes0), int(seconds0))
            effect_time_str1 = "{:02d}:{:02d}".format(int(minutes1), int(seconds1))
            effect_time_str2 = "{:02d}:{:02d}".format(int(minutes2), int(seconds2))
            self._tmp['RNG'] += f"Monster Extract sets time to {effect_time_str0}, {effect_time_str1} or {effect_time_str2} (each 33.3%)"

        elif self._critical_only_time_flag or self._critical_health_time_flag or self._critical_health_level_time_flag:
            # if time critical, generate string for the time addition
            self._tmp['RNG'] += f"If there's a critical hit, duration gets a {crit_time_string} increase"

        # non-RNG effect time
        minutes, seconds = divmod(self._tmp['EffectTime'], 60)
        effect_time_str = "{:02d}:{:02d}".format(int(minutes), int(seconds))

        # heart recovery formatting

        # unsure about its use anymore
        quarter_heart_map = {
            0: '',
            1: '¼',
            2: '½',
            3: '¾'
        }

        if self._monster_extract_only_health_random_flag or self._monster_extract_health_level_random_flag:
            # if monster extract affects health, generate string for both bad and good case
            whole_heart0, quarter_heart0 = divmod(self._tmp['Monster Extract']['HitPointRecover'][0], 4)
            whole_heart0, quarter_heart0 = int(whole_heart0), int(quarter_heart0)
            if effect == 'LifeMaxUp' or self._tmp['Monster Extract']['HitPointRecover'][0] == 120.0:
                heart_str0 = '♥ Full Recovery'
            else:
                heart_str0 = '♥' * whole_heart0
                if quarter_heart0:
                    heart_str0 += quarter_heart_map[quarter_heart0]+'♥'
            heart_str0 = "None" if heart_str0 == "" else heart_str0
            if self._monster_extract_only_health_random_flag or self._monster_extract_health_level_random_flag:
                # covers both cases of getting or not full health 
                if self._tmp['HitPointRecover'] + int(self.effect['LifeRecover'].get('SuperSuccessAddVolume') / 4) >= 120:
                    self._tmp['RNG'] += f"Monster Extract sets health recovery to {heart_str0}, either adds Full Recovery"
                else:
                    self._tmp['RNG'] += f"Monster Extract sets health recovery to {heart_str0}, either adds {int(self.effect['LifeRecover'].get('SuperSuccessAddVolume') / 4)} Hearts"

        elif self._critical_only_health_flag or self._critical_health_level_flag or self._critical_health_level_time_flag or self._critical_health_time_flag:
            # if critical effects health, generate string for health addition
            # covers both cases of getting or not full health
            if self._tmp['HitPointRecover'] + self.effect['LifeRecover'].get('SuperSuccessAddVolume') >= 120:
                self._tmp['RNG'] += f"If there's a critical hit, adds Full Recovery"
            else:
                self._tmp['RNG'] += f"If there's a critical hit, adds {int(self.effect['LifeRecover'].get('SuperSuccessAddVolume') / 4)} Hearts"

        # calculate heart amount        
        heart_amount = round(self._tmp['HitPointRecover'] / 4, 2)
        # remove unnecessary digits
        if heart_amount.is_integer():
            heart_amount = int(heart_amount)
        elif (heart_amount * 2).is_integer():
            heart_amount = round(heart_amount, 1) 
    
        # if Extra Hearts or Full Recovery, generate string for Full Recovery
        if effect == 'LifeMaxUp' or self._tmp['HitPointRecover'] == self.effect['LifeRecover'].get('MaxLv'):
            heart_str = "Full Recovery"
        # if no recovery, generate None string
        elif heart_amount == 0:
            heart_str = "None"
        elif heart_amount < 2:
            heart_str = str(heart_amount) + " Heart"
        else:
            heart_str = str(heart_amount) + " Hearts"

        # effect level formatting

        if effect == "LifeMaxUp":
            # needs specific string format for "Extra Heart(s)"
            if self._monster_extract_only_level_flag or self._monster_extract_health_level_random_flag:
                self._tmp['RNG'] += f"Monster Extract sets meal effect to {int(self._tmp['Monster Extract']['EffectLevel'][0] / 4)} Extra Heart, either adds {int((self._tmp['Monster Extract']['EffectLevel'][2] - self._tmp['Monster Extract']['EffectLevel'][1]) / 4)} Extra Heart to the meal effect'"
            elif self._critical_only_level_flag or self._critical_health_level_flag or self._critical_health_level_time_flag:
                self._tmp['RNG'] += f"If there's a critical hit, adds {int((self._tmp['Critical']['EffectLevel'][1] - self._tmp['Critical']['EffectLevel'][0]) / 4)} Extra Heart to the meal effect"
            level_str = str(int(self._tmp['EffectLevel'] / 4)) + " Extra Heart(s)"
            effect_time_str = "None"
        elif effect == "StaminaRecover":
            # needs specific string format for "Stamina Segment(s)"
            if self._monster_extract_only_level_flag or self._monster_extract_health_level_random_flag:
                self._tmp['RNG'] += f"Monster Extract sets meal effect to {self._tmp['Monster Extract']['EffectLevel'][0]} Stamina Segment, either adds {self._tmp['Monster Extract']['EffectLevel'][2] - self._tmp['Monster Extract']['EffectLevel'][1]} Stamina Segments to the meal effect"
            elif self._critical_only_level_flag or self._critical_health_level_flag or self._critical_health_level_time_flag:
                self._tmp['RNG'] += f"If there's a critical hit, adds {self._tmp['Critical']['EffectLevel'][1] - self._tmp['Critical']['EffectLevel'][0]} Stamina Segments to the meal effect"
            level_str = str(int(self._tmp['EffectLevel'])) + " Stamina Segment(s)"
            effect_time_str = "None"
        elif effect == "ExStaminaMaxUp":
            # needs specific string format for "Extra Stamina Segment(s)"
            if self._monster_extract_only_level_flag or self._monster_extract_health_level_random_flag:
                self._tmp['RNG'] += f"Monster Extract sets meal effect to {self._tmp['Monster Extract']['EffectLevel'][0]} Extra Stamina Segment, either adds {self._tmp['Monster Extract']['EffectLevel'][2] - self._tmp['Monster Extract']['EffectLevel'][1]} Extra Stamina Segments to the meal effect"
            elif self._critical_only_level_flag or self._critical_health_level_flag or self._critical_health_level_time_flag:
                self._tmp['RNG'] += f"If there's a critical hit, adds {self._tmp['Critical']['EffectLevel'][1] - self._tmp['Critical']['EffectLevel'][0]} Extra Stamina Segments to the meal effect"
            level_str = str(int(self._tmp['EffectLevel'])) + " Extra Stamina Segment(s)"
            effect_time_str = "None"
        elif effect == "LifeRepair":
            # needs specific string format for "Ungloomed Heart(s)"
            if self._monster_extract_only_level_flag or self._monster_extract_health_level_random_flag:
                self._tmp['RNG'] += f"Monster Extract sets meal effect to {int(self._tmp['Monster Extract']['EffectLevel'][0] / 4)} Ungloomed Heart, either adds {int((self._tmp['Monster Extract']['EffectLevel'][2] - self._tmp['Monster Extract']['EffectLevel'][1]) / 4)} Ungloomed Heart to the meal effect"
            elif self._critical_only_level_flag or self._critical_health_level_flag or self._critical_health_level_time_flag:
                self._tmp['RNG'] += f"If there's a critical hit, adds {int((self._tmp['Critical']['EffectLevel'][1] - self._tmp['Critical']['EffectLevel'][0]) / 4)} Ungloomed Heart to the meal effect"
            level_str = str(int(self._tmp['EffectLevel'] / 4)) + " Ungloomed Hearts"
            effect_time_str = "None"
        else:
            # regular level string format
            if self._monster_extract_only_level_flag or self._monster_extract_health_level_random_flag:
                self._tmp['RNG'] += f"Monster Extract sets effect level to {self._tmp['Monster Extract']['EffectLevel'][0]}, either adds {self._tmp['Monster Extract']['EffectLevel'][2] - self._tmp['Monster Extract']['EffectLevel'][1]} level(s) to the effect"
            elif self._critical_only_level_flag or self._critical_health_level_flag or self._critical_health_level_time_flag:
                self._tmp['RNG'] += f"If there's a critical hit, adds {self._tmp['Critical']['EffectLevel'][1] - self._tmp['Critical']['EffectLevel'][0]} level(s) to the effect"
            level_str = str(self._tmp['EffectLevel'])

        # description

        locale_actor_caption = self._locale_dict['Meal'][f'{result_actor_name}_Caption'][self.area_lang]
        locale_effect_desc = ''

        if effect:
            effect_desc_key = effect
            # handle elixir description
            if result_actor_name == 'Item_Cook_C_17':
                effect_desc_key += '_MedicineDesc'
            else:
                effect_desc_key += '_Desc'
            
            if self.effect[effect].get('MaxLv') <= 3 and self._tmp['EffectLevel'] > 1:
                effect_desc_key += '_{:02d}'.format(self._tmp['EffectLevel'])
            locale_effect_desc = self._locale_dict['Effect'][effect_desc_key][self.area_lang]

        local_meal_desc = (locale_effect_desc +'\n' + locale_actor_caption).strip()
        
        # result

        # almost final dict
        self._result = {
            'Meal name': f"{locale_meal_name} ({self._tmp['Recipe']['ResultActorName']})",
            'Actor name': self._tmp['Recipe']['ResultActorName'],
            'Recipe number': self._tmp['Recipe']['PictureBookNum'],
            'Health recovery': heart_str,
            'Effect': f'{locale_buff_name} ({effect if effect != None else ""})'.replace(' ()', ''),
            'Effect duration': effect_time_str,
            'Effect level': level_str,
            'Critical rate': str(min(self._tmp['SuperSuccessRate'], 100)) + "%",
            'Sell price': str(self._tmp['SellingPrice']) + " Rupees",
            'Description': local_meal_desc.replace('\n', ' '),
        }

        # make sure None duration and None level if None effect
        if self._result['Effect'] == None or self._result['Effect'] == "None":
            self._result['Effect duration'] = "None"
            self._result['Effect level'] = "None"

        if self._tmp['RNG']:
            # handles critical final string
            if "If there's a critical hit, " in self._tmp['RNG']:
                crit_text = "If there's a critical hit, "
                part_amount = self._tmp['RNG'].count("If there's a critical hit, ")
                # if only one critical possibility
                if part_amount == 1:
                    crit_text += self._tmp['RNG'].split("If there's a critical hit, ")[1]
                # if two critical possibilities
                elif part_amount == 2:
                    crit_text += "either " + self._tmp['RNG'].split("If there's a critical hit, ")[1] + ", either " + self._tmp['RNG'].split("If there's a critical hit, ")[2]
                # if all three critical possibilities
                else:
                    crit_text += "either " + self._tmp['RNG'].split("If there's a critical hit, ")[1] + ", either " + self._tmp['RNG'].split("If there's a critical hit, ")[2]+ ", either " + self._tmp['RNG'].split("If there's a critical hit, ")[3]
                self._result['RNG'] = crit_text

            # handles monster extract final string
            else:
                me_text = "Monster Extract "
                # need to separate cases for monster extract time or not because of the "and" it implies
                if self._monster_extract_time_flag:
                    part_amount = self._tmp['RNG'].count("Monster Extract ")
                    # if only one monster extract non-time change
                    if part_amount == 1:
                        me_text += self._tmp['RNG'].split('Monster Extract ')[1]
                    # if all two monster extract non-time changes
                    else:
                        me_text += self._tmp['RNG'].split('Monster Extract ')[1] + " and, either " + self._tmp['RNG'].split('Monster Extract ')[2]
                else:
                    part_amount = self._tmp['RNG'].count("Monster Extract ")
                    # if only one monster extract non-time change
                    if part_amount == 1:
                        me_text += "either " + self._tmp['RNG'].split('Monster Extract ')[1]
                    # if all two monster extract non-time changes
                    else:
                        me_text += "either " + self._tmp['RNG'].split('Monster Extract ')[1] + ", either " + self._tmp['RNG'].split('Monster Extract ')[2]
                self._result['RNG'] = me_text

        # Elixir actor name and cooking book data
        if result_actor_name == 'Item_Cook_C_17':
            self._result['Actor name'] += '_' + self._tmp['Effect']
            self._result['Recipe number'] = self.recipe_card_table.index(self._result['Actor name']) + 1

        # useless now since in meal name
        del self._result['Actor name']

        # generate final dictionary with the output of the cooking algorithm
        self.output = {}
        for k, v in self._result.items():
            self.output[k] = v
        
if __name__ == "__main__":
    meal = TotKCookSim()
    output = meal.cook(["Apple"])
    print(output)