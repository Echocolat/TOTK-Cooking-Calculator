# this is largely inspired and copied from https://github.com/KingFooZQ/Totk-Cooking-Simulator/blob/main/simulator.py
# it was also updated to be accurate following the Cooking discoveries made in the TotK datamining server (https://discord.gg/wsXNa2MGwQ) 08/18/2024

import json
import math
import copy

class TotKCookSim():

    def __init__(self):
        self._load_data()

    def _load_data(self):

        self.area_lang = 'USen'

        with open('Data/SystemData.json', 'r', encoding = 'UTF-8') as json_file:
            self.system_data = json.loads(json_file.read())

        with open('Data/RecipeData.json', 'r', encoding = 'UTF-8') as json_file:
            self.recipes = json.loads(json_file.read())

        with open('Data/SingleRecipeData.json', 'r', encoding = 'UTF-8') as json_file:
            self.recipes_single = json.loads(json_file.read())

        with open('Data/RecipeCardData.json', 'r', encoding = 'UTF-8') as json_file:
            self.recipe_card_table = json.loads(json_file.read())


        self.material = {}
        with open('Data/MaterialData.json', 'r', encoding = 'UTF-8') as json_file:
            materials = json.loads(json_file.read())
            for item in materials:
                self.material[item['ActorName']] = item
        
        self.effect = {}
        with open('Data/EffectData.json', 'r', encoding = "UTF-8") as json_file:
            effects = json.loads(json_file.read())
            for item in effects:
                self.effect[item['EffectType']] = item

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
        self._tmp = {}
        self.output = {}
        self._material(materials)
        self._recipe()
        self._hitpoint_recover()
        self._effect()
        self._sell_price()
        self._super_success_rate()
        self._monster_extract()
        self._critical()
        self._spice()
        self._after_spice()
        self._special_deal()
        self._english()
        return self.output

    def _material(self, materials: list):
        materials_list = []
        for i in materials:
            actor_name = self._index_material_name[i]
            materials_list.append(self.material[actor_name])
        self._tmp['Materials'] = materials_list
        return
    
    def _recipe(self):
        self._tmp['Recipe'] = {
            "ResultActorName": "Item_Cook_O_01",
            "Recipe": "CookEnemy or CookInsect",
            "PictureBookNum": 145,
            "SingleRecipeMaterialNum": 1
        }
        materials_list = self._tmp['Materials']
        materials_name_tag = []
        for material in materials_list:
            actor_name = material['ActorName']
            cook_tag = material['CookTag']
            if (actor_name, cook_tag) not in materials_name_tag:
                materials_name_tag.append((actor_name, cook_tag))

        if len(materials_name_tag) == 1:
            for recipe in self.recipes_single:
                m_copy = copy.copy(materials_name_tag)
                if recipe['ResultActorName'] == self.system_data['FailActorName']:
                    self._tmp['Recipe'] = recipe
                recipe_str = recipe['Recipe']
                parts_list = recipe_str.split(' or ')

                all_ok = False
                for or_part in parts_list:
                    material = m_copy[0]
                    if or_part == material[0] or or_part == material[1]:
                        m_copy.pop(0)
                        all_ok = True
                        break
                if all_ok:
                    self._tmp['Recipe'] = recipe
                    return recipe
        
        else:
            for recipe in self.recipes:
                m_copy = copy.copy(materials_name_tag)
                if recipe['ResultActorName'] == self.system_data['FailActorName']:
                    self._tmp['Recipe'] = recipe
                recipe_str = recipe['Recipe']
                and_parts = recipe_str.split(' + ')
                parts_list = [i.split(' or ') for i in and_parts]
                if len(parts_list) > len(materials_name_tag):
                    continue

                all_ok = True
                for and_part in parts_list:
                    and_ok = False
                    for or_part in and_part:
                        for index in range(len(m_copy)):
                            material = m_copy[index]
                            if or_part == material[0] or or_part == material[1]:
                                m_copy.pop(index)
                                and_ok = True
                                break
                        if and_ok:
                            break
                    if not and_ok:
                        all_ok = False
                        break
                if all_ok:
                    self._tmp['Recipe'] = recipe
                    return recipe
        
        if 'CookSpice' in [i[1] for i in materials_name_tag]:
            for recipe in self.recipes_single:
                m_copy = copy.copy(materials_name_tag)
                if recipe['ResultActorName'] == self.system_data['FailActorName']:
                    self._tmp['Recipe'] = recipe
                recipe_str = recipe['Recipe']
                parts_list = recipe_str.split(' or ')

                all_ok = False
                for or_part in parts_list:
                    for index in range(len(m_copy)):
                        material = m_copy[index]
                        if or_part == material[0] or or_part == material[1]:
                            m_copy.pop(index)
                            all_ok = True
                            break
                if all_ok:
                    self._tmp['Recipe'] = recipe
                    return recipe
            
        return None
    
    def _hitpoint_recover(self):
        materials_list = self._tmp['Materials']
        recipe = self._tmp['Recipe']
        hitpoint_recover = 0
        for material in materials_list:
            hitpoint_recover += material.get('HitPointRecover', 0)
        
        if recipe['ResultActorName'] == self.system_data['FailActorName']:
            life_recover_rate = self.system_data['SubtleLifeRecoverRate']
        else:
            life_recover_rate = self.system_data['LifeRecoverRate']
        hitpoint_recover = hitpoint_recover * life_recover_rate
        self._tmp['HitPointRecover'] = hitpoint_recover
        return

    def _effect(self):
        materials_list = self._tmp['Materials']
        recipe = self._tmp['Recipe']
        set_effect_flag = False
        effect_level = 0
        effect_type = None
        effect_time = 0
        bonus_time = 0
        for mat in materials_list:
            if mat.get('CookTag') == "CookEnemy":
                bonus_time += mat.get('SpiceBoostEffectiveTime', 0)
        for effect in self.effect:
            effect_materials_num = len([mat for mat in materials_list if mat.get('CureEffectType', "None") == effect])
            if effect_materials_num > 0:
                if set_effect_flag:
                    effect_level = 0
                    effect_type = None
                    effect_time = 0
                else:
                    effect_type = effect
                potency_sum = 0
                effect_time += bonus_time
                for mat in materials_list:
                    if mat.get('CureEffectType', "None") == effect:
                        potency_sum += mat.get('CureEffectLevel', 0)
                    effect_time += mat.get('CureEffectiveTime', 900) / 30
                effect_time += effect_materials_num * self.effect[effect].get('BaseTime', 0)
                effect_level += self.effect[effect].get('Rate', 0) * potency_sum
                effect_level = min(effect_level, self.effect[effect].get('MaxLv'))
                set_effect_flag = True
        
        if recipe['ResultActorName'] == self.system_data['FairyActorName']:
            effect_type = None
            effect_level = 0.0
            effect_time = 0

        self._tmp['Effect'] = effect_type
        self._tmp['EffectLevel'] = effect_level
        self._tmp['EffectTime'] = effect_time

    def _sell_price(self):
        selling_price = 0
        materials_list = self._tmp['Materials']
        for material in materials_list:
            if material.get('CookLowPrice', False):
                selling_price += 1
            else:
                selling_price += material.get('SellingPrice', 0)
        for item in self.system_data['PriceRateList']:
            if item['MaterialNum'] == len(materials_list):
                self._tmp['SellingPrice'] = math.floor(selling_price * item['Rate'])
                return 
        return

    def _super_success_rate(self):
        materials_set = set()
        self._tmp['SuperSuccessRate'] = 0
        materials_list = self._tmp['Materials']
        for material in materials_list:
            self._tmp['SuperSuccessRate'] = max(self._tmp['SuperSuccessRate'], material.get('SpiceBoostSuccessRate', 0))
            materials_set.add(material['ActorName'])
        
        for item in self.system_data['SuperSuccessRateList']:
            if item['MaterialTypeNum'] == len(materials_set):
                self._tmp['SuperSuccessRate'] += item['Rate']
                return

    def _monster_extract(self):
        materials_list = self._tmp['Materials']
        effect = self._tmp['Effect']
        effect_level = self._tmp['EffectLevel']
        effect_time = self._tmp['EffectTime']
        hitpoint_recover = self._tmp['HitPointRecover']
        self._monster_extract_time_flag = False
        self._monster_extract_only_health_up_flag = False
        self._monster_extract_only_health_random_flag = False
        self._monster_extract_health_level_random_flag = False
        self._monster_extract_only_level_flag = False
        self._monster_extract_flag = False
        if self._tmp['Recipe']['ResultActorName'] in [self.system_data['FailActorName'], "Item_Cook_O_02"]:
            return

        for mat in materials_list:
            if mat.get("ActorName") == "Item_Material_08":
                self._monster_extract_flag = True
        if self._monster_extract_flag:
            self._tmp['Monster Extract'] = {}
            if effect != None and effect_time > 0:
                # monster extract sets time
                self._monster_extract_time_flag = True
                self._tmp['Monster Extract']['EffectTime'] = [60, 600, 1800]
            if (hitpoint_recover == 0 and effect != None) or effect == 'LifeMaxUp':
                # if the meal is not regenerative but has an effect, or is a hearty meal
                self._monster_extract_only_level_flag = True
                self._tmp['Monster Extract']['EffectLevel'] = [self.effect[effect].get('MinLv'), effect_level + self.effect[effect].get('SuperSuccessAddVolume')]
            elif (hitpoint_recover == 0 and effect != None):
                # if the meal is not regenerative and has no effect (?)
                self._monster_extract_only_health_up_flag = True
                self._tmp['Monster Extract']['HitPointRecover'] = hitpoint_recover + self.effect['LifeRecover'].get('SuperSuccessAddVolume')
            elif effect != None:
                # if the meal is regenerative and has an effect (that is not hearty)
                self._monster_extract_health_level_random_flag = True
                self._tmp['Monster Extract']['HitPointRecover'] = [1, hitpoint_recover, hitpoint_recover + self.effect['LifeRecover'].get('SuperSuccessAddVolume')]
                self._tmp['Monster Extract']['EffectLevel'] = [self.effect[effect].get('MinLv'), effect_level, effect_level + self.effect[effect].get('SuperSuccessAddVolume')]
            else:
                # if the meal is regenerative with no effect
                self._monster_extract_only_health_random_flag = True
                self._tmp['Monster Extract']['HitPointRecover'] = [1, hitpoint_recover + self.effect['LifeRecover'].get('SuperSuccessAddVolume')]

    def _critical(self):
        effect = self._tmp['Effect']
        effect_level = self._tmp['EffectLevel']
        effect_time = self._tmp['EffectTime']
        hitpoint_recover = self._tmp['HitPointRecover']
        self._critical_only_time_flag = False
        self._critical_only_health_flag = False
        self._critical_health_level_flag = False
        self._critical_health_time_flag = False
        self._critical_health_level_time_flag = False
        self._critical_only_level_flag = False
        self._critical_flag = False
        if self._tmp['Recipe']['ResultActorName'] in [self.system_data['FailActorName'], "Item_Cook_O_02"]:
            return

        if not self._monster_extract_flag:
            self._critical_flag = True
            self._tmp['Critical'] = {}
            if effect_level <= 1.0:
                effect_level, self._tmp['EffectLevel'] = 1.0, 1.0
            if effect == None:
                # health crit
                self._critical_only_health_flag = True
                self._tmp['Critical']['HitPointRecover'] = [hitpoint_recover, hitpoint_recover + self.effect['LifeRecover'].get('SuperSuccessAddVolume')]
            elif effect == "LifeMaxUp":
                # level crit
                self._critical_only_level_flag = True
                self._tmp['Critical']['EffectLevel'] = [effect_level, effect_level + self.effect[effect].get('SuperSuccessAddVolume')]
            elif effect in ['StaminaRecover', 'ExStaminaMaxUp']:
                if effect_level >= self.effect[effect].get('MaxLv'):
                    # health crit
                    self._critical_only_health_flag = True
                    self._tmp['Critical']['HitPointRecover'] = [hitpoint_recover, hitpoint_recover + self.effect['LifeRecover'].get('SuperSuccessAddVolume')]
                else:
                    # health or level crit
                    self._critical_health_level_flag = True
                    self._tmp['Critical']['HitPointRecover'] = [hitpoint_recover, hitpoint_recover + self.effect['LifeRecover'].get('SuperSuccessAddVolume')]
                    self._tmp['Critical']['EffectLevel'] = [effect_level, effect_level + self.effect[effect].get('SuperSuccessAddVolume')]
            elif effect_level >= self.effect[effect].get('MaxLv'):
                if hitpoint_recover >= self.effect['LifeRecover'].get('MaxLv'):
                    # time crit
                    self._critical_only_time_flag = True
                    self._tmp['Critical']['EffectTime'] = [effect_time, effect_time + self.system_data.get('SuperSuccessAddEffectiveTime')]
                else:
                    # health or time crit
                    self._critical_health_time_flag = True
                    self._tmp['Critical']['HitPointRecover'] = [hitpoint_recover, hitpoint_recover + self.effect['LifeRecover'].get('SuperSuccessAddVolume')]
                    self._tmp['Critical']['EffectTime'] = [effect_time, effect_time + self.system_data.get('SuperSuccessAddEffectiveTime')]
            elif hitpoint_recover >= self.effect['LifeRecover'].get('MaxLv'):
                # health or level crit
                self._critical_health_level_flag = True
                self._tmp['Critical']['HitPointRecover'] = [hitpoint_recover, hitpoint_recover + self.effect['LifeRecover'].get('SuperSuccessAddVolume')]
                self._tmp['Critical']['EffectLevel'] = [effect_level, effect_level + self.effect[effect].get('SuperSuccessAddVolume')]
            else:
                # health or level or time crit
                self._critical_health_level_time_flag = True
                self._tmp['Critical']['HitPointRecover'] = [hitpoint_recover, hitpoint_recover + self.effect['LifeRecover'].get('SuperSuccessAddVolume')]
                self._tmp['Critical']['EffectLevel'] = [effect_level, effect_level + self.effect[effect].get('SuperSuccessAddVolume')]
                self._tmp['Critical']['EffectTime'] = [effect_time, effect_time + self.system_data.get('SuperSuccessAddEffectiveTime')]

    def _spice(self):
        if self._tmp['Recipe']['ResultActorName'] == self.system_data['FailActorName']:
            return
        effect = self._tmp['Effect']
        materials_list = self._tmp['Materials']
        effect_level = self._tmp['EffectLevel']
        effect_time = self._tmp['EffectTime']
        hitpoint_recover = self._tmp['HitPointRecover']
        for material in materials_list:
            if material.get('CookTag') != "CookEnemy":
                # health spice
                if self._critical_health_level_flag or self._critical_health_level_time_flag or self._critical_health_time_flag or self._critical_only_health_flag or self._monster_extract_only_health_random_flag:
                    self._tmp['Critical']['HitPointRecover'] = [self._tmp['Critical']['HitPointRecover'][0] + material.get('SpiceBoostHitPointRecover', 0), self._tmp['Critical']['HitPointRecover'][1] + material.get('SpiceBoostHitPointRecover', 0)]
                elif self._monster_extract_health_level_random_flag:
                    self._tmp['Monster Extract']['HitPointRecover'] = [self._tmp['Monster Extract']['HitPointRecover'][0] + material.get('SpiceBoostHitPointRecover', 0), self._tmp['Monster Extract']['HitPointRecover'][1] + material.get('SpiceBoostHitPointRecover', 0), self._tmp['Monster Extract']['HitPointRecover'][2] + material.get('SpiceBoostHitPointRecover', 0)]
                hitpoint_recover += material.get('SpiceBoostHitPointRecover', 0)
                # time spice
                if self._critical_only_time_flag or self._critical_health_time_flag or self._critical_health_level_time_flag:
                    self._tmp['Critical']['EffectTime'] = [self._tmp['Critical']['EffectTime'][0] + material.get('SpiceBoostEffectiveTime', 0), self._tmp['Critical']['EffectTime'][1] + material.get('SpiceBoostEffectiveTime', 0)]
                elif self._monster_extract_time_flag:
                    self._tmp['Monster Extract']['EffectTime'] = [self._tmp['Monster Extract']['EffectTime'][0] + material.get('SpiceBoostEffectiveTime', 0), self._tmp['Monster Extract']['EffectTime'][1] + material.get('SpiceBoostEffectiveTime', 0), self._tmp['Monster Extract']['EffectTime'][2] + material.get('SpiceBoostEffectiveTime', 0)]
                effect_time += material.get('SpiceBoostEffectiveTime', 0)
            if material.get('CookTag') == "CookSpice":
                # yellow health spice
                if effect == "LifeMaxUp":
                    if self._critical_only_level_flag or self._critical_health_level_flag or self._critical_health_level_time_flag:
                        self._tmp['Critical']['EffectLevel'] = [self.tmp['Critical']['EffectLevel'][0] + material.get('SpiceBoostMaxHeartLevel', 0), self.tmp['Critical']['EffectLevel'][1] + material.get('SpiceBoostMaxHeartLevel', 0)]
                    elif self._monster_extract_health_level_random_flag or self._monster_extract_only_level_flag:
                        self._tmp['Monster Extract']['EffectLevel'] = [self.tmp['Monster Extract']['EffectLevel'][0] + material.get('SpiceBoostMaxHeartLevel', 0), self.tmp['Monster Extract']['EffectLevel'][1] + material.get('SpiceBoostMaxHeartLevel', 0), self.tmp['Monster Extract']['EffectLevel'][2] + material.get('SpiceBoostMaxHeartLevel', 0)]
                    effect_level += material.get('SpiceBoostMaxHeartLevel', 0)
                # tamina spice
                elif effect in ['StaminaRecover', 'ExStaminaMaxUp']:
                    if self._critical_only_level_flag or self._critical_health_level_flag or self._critical_health_level_time_flag:
                        self._tmp['Critical']['EffectLevel'] = [self.tmp['Critical']['EffectLevel'][0] + material.get('SpiceBoostStaminaLevel', 0), self.tmp['Critical']['EffectLevel'][1] + material.get('SpiceBoostStaminaLevel', 0)]
                    elif self._monster_extract_health_level_random_flag or self._monster_extract_only_level_flag:
                        self._tmp['Monster Extract']['EffectLevel'] = [self.tmp['Monster Extract']['EffectLevel'][0] + material.get('SpiceBoostStaminaLevel', 0), self.tmp['Monster Extract']['EffectLevel'][1] + material.get('SpiceBoostStaminaLevel', 0), self.tmp['Monster Extract']['EffectLevel'][2] + material.get('SpiceBoostStaminaLevel', 0)]
                    effect_level += material.get('SpiceBoostStaminaLevel', 0)

        self._tmp['EffectLevel'] = effect_level
        self._tmp['EffectTime'] = effect_time
        self._tmp['HitPointRecover'] = hitpoint_recover

    def _after_spice(self):
        recipe = self._tmp['Recipe']
        effect = self._tmp.get('Effect')
        # bonus time
        if self._monster_extract_time_flag:
            self._tmp['Monster Extract']['EffectTime'] = [min(self._tmp['Monster Extract']['EffectTime'][0] + recipe.get('BonusTime', 0), 1800), min(self._tmp['Monster Extract']['EffectTime'][1] + recipe.get('BonusTime', 0), 1800), min(self._tmp['Monster Extract']['EffectTime'][2] + recipe.get('BonusTime', 0), 1800)]
        elif self._critical_only_time_flag or self._critical_health_time_flag or self._critical_health_level_time_flag:
            self._tmp['Critical']['EffectTime'] = [min(self._tmp['Critical']['EffectTime'][0] + recipe.get('BonusTime', 0), 1800), min(self._tmp['Critical']['EffectTime'][1] + recipe.get('BonusTime', 0), 1800)]
        self._tmp['EffectTime'] = min(self._tmp['EffectTime'] + recipe.get('BonusTime', 0), 1800)
        # bonus health
        if self._critical_health_level_flag or self._critical_health_level_time_flag or self._critical_health_time_flag or self._critical_only_health_flag or self._monster_extract_only_health_random_flag:
            self._tmp['Critical']['HitPointRecover'] = [min(120, self._tmp['Critical']['HitPointRecover'][0] + recipe.get('BonusHeart', 0)), min(120, self._tmp['Critical']['HitPointRecover'][1] + recipe.get('BonusHeart', 0))]
            self._tmp['Critical']['HitPointRecover'] = [self.effect['LifeRecover'].get('MaxLv') if self._tmp['Critical']['HitPointRecover'][0] == 120 else self._tmp['Critical']['HitPointRecover'][0], self.effect['LifeRecover'].get('MaxLv') if self._tmp['Critical']['HitPointRecover'][1] == 120 else self._tmp['Critical']['HitPointRecover'][1]]
            if effect == 'LifeMaxUp':
                self._tmp['Critical']['HitPointRecover'] = [self.effect['LifeRecover'].get('MaxLv'), self.effect['LifeRecover'].get('MaxLv')]
            if effect == None:
                self._tmp['Critical']['HitPointRecover'] = [1 if self._tmp['Critical']['HitPointRecover'][0] == 0 else self._tmp['Critical']['HitPointRecover'][0], 1 if self._tmp['Critical']['HitPointRecover'][1] == 0 else self._tmp['Critical']['HitPointRecover'][1]]
        elif self._monster_extract_health_level_random_flag:
            self._tmp['Monster Extract']['HitPointRecover'] = [min(120, self._tmp['Monster Extract']['HitPointRecover'][0] + recipe.get('BonusHeart', 0)), min(120, self._tmp['Monster Extract']['HitPointRecover'][1] + recipe.get('BonusHeart', 0)), min(120, self._tmp['Monster Extract']['HitPointRecover'][2] + recipe.get('BonusHeart', 0))]
            self._tmp['Monster Extract']['HitPointRecover'] = [self.effect['LifeRecover'].get('MaxLv') if self._tmp['Monster Extract']['HitPointRecover'][0] == 120 else self._tmp['Monster Extract']['HitPointRecover'][0], self.effect['LifeRecover'].get('MaxLv') if self._tmp['Monster Extract']['HitPointRecover'][1] == 120 else self._tmp['Monster Extract']['HitPointRecover'][1], self.effect['LifeRecover'].get('MaxLv') if self._tmp['Monster Extract']['HitPointRecover'][2] == 120 else self._tmp['Monster Extract']['HitPointRecover'][2]]
            if effect == 'LifeMaxUp':
                self._tmp['Monster Extract']['HitPointRecover'] = [self.effect['LifeRecover'].get('MaxLv'), self.effect['LifeRecover'].get('MaxLv'), self.effect['LifeRecover'].get('MaxLv')]
            if effect == None:
                self._tmp['Monster Extract']['HitPointRecover'] = [1 if self._tmp['Monster Extract']['HitPointRecover'][0] == 0 else self._tmp['Monster Extract']['HitPointRecover'][0], 1 if self._tmp['Monster Extract']['HitPointRecover'][1] == 0 else self._tmp['Monster Extract']['HitPointRecover'][1], 1 if self._tmp['Monster Extract']['HitPointRecover'][2] == 0 else self._tmp['Monster Extract']['HitPointRecover'][2]]
        self._tmp['HitPointRecover'] = min(120, self._tmp['HitPointRecover'] + recipe.get('BonusHeart', 0))
        self._tmp['HitPointRecover'] = self.effect['LifeRecover'].get('MaxLv') if self._tmp['HitPointRecover'] == 120 else self._tmp['HitPointRecover']
        if effect == None:
            self._tmp['HitPointRecover'] = 1 if self._tmp['HitPointRecover'] == 0 else self._tmp['HitPointRecover']
        # clamping effect
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
            self._tmp['EffectLevel'] = min(self.effect[effect].get('MaxLv'), self._tmp['EffectLevel'])
            self._tmp['EffectLevel'] = 1.0 if self._tmp['EffectLevel'] <= 1.0 and self._tmp['EffectLevel'] > 0 else self._tmp['EffectLevel']
            if effect in ['LifeMaxUp', 'LifeRepair']:
                self._tmp['EffectLevel'] = 4 * round(self._tmp['EffectLevel'] / 4)
                self._tmp['EffectLevel'] = 4 if self._tmp['EffectLevel'] <= 4.0 and self._tmp['EffectLevel'] > 0 else self._tmp['EffectLevel']
            self._tmp['EffectLevel'] = math.floor(self._tmp['EffectLevel'])

    def _special_deal(self):
        self._tmp['RNG'] = ''

        # special deal
        recipe = self._tmp['Recipe']
        if recipe['ResultActorName'] == 'Item_Cook_O_02':
            self._tmp['HitPointRecover'] = self.system_data['FailLifeRecover']
            self._tmp['Effect'] = None
            self._tmp['EffectTime'] = 0
            self._tmp['EffectLevel'] = 0
            self._tmp['SellingPrice'] = 2
        elif recipe['ResultActorName'] == self.system_data['FailActorName']:
            self._tmp['HitPointRecover'] = self.system_data['SubtleLifeRecover']
            self._tmp['Effect'] = None
            self._tmp['EffectTime'] = 0
            self._tmp['EffectLevel'] = 0
            self._tmp['SellingPrice'] = 2
        elif recipe['ResultActorName'] == self.system_data['FairyActorName']:
            self._tmp['SellingPrice'] = 2

    def _english(self):
        result_actor_name = self._tmp['Recipe']['ResultActorName']
        effect = self._tmp.get('Effect')
        locale_actor_name = self._locale_dict['Meal'][f'{result_actor_name}_Name'][self.area_lang]
        
        # name
        locale_effect_name = ''
        locale_buff_name = ''
        if effect:
            locale_effect_name = self._locale_dict['Effect'][effect+'_Name'][self.area_lang]
            locale_buff_name = self._locale_dict['Buff'][effect][self.area_lang]
            locale_meal_name = locale_effect_name + ' ' + locale_actor_name
        else:
            locale_meal_name = locale_actor_name
        if not locale_buff_name:
            locale_buff_name = "None"

        # effect time
        crit_time_min, crit_time_sec = divmod(self.system_data['SuperSuccessAddEffectiveTime'], 60)
        crit_time_string = "{:02d}:{:02d}".format(int(crit_time_min), int(crit_time_sec))
        if self._monster_extract_time_flag:
            minutes0, seconds0 = divmod(self._tmp['Monster Extract']['EffectTime'][0], 60)
            minutes1, seconds1 = divmod(self._tmp['Monster Extract']['EffectTime'][1], 60)
            minutes2, seconds2 = divmod(self._tmp['Monster Extract']['EffectTime'][2], 60)
            effect_time_str0 = "{:02d}:{:02d}".format(int(minutes0), int(seconds0))
            effect_time_str1 = "{:02d}:{:02d}".format(int(minutes1), int(seconds1))
            effect_time_str2 = "{:02d}:{:02d}".format(int(minutes2), int(seconds2))
            self._tmp['RNG'] += f"Monster Extract sets time to {effect_time_str0}, {effect_time_str1} or {effect_time_str2} (each 33.3%)"
        elif self._critical_only_time_flag or self._critical_health_time_flag or self._critical_health_level_time_flag:
            minutes0, seconds0 = divmod(self._tmp['Critical']['EffectTime'][0], 60)
            minutes1, seconds1 = divmod(self._tmp['Critical']['EffectTime'][1], 60)
            effect_time_str0 = "{:02d}:{:02d}".format(int(minutes0), int(seconds0))
            effect_time_str1 = "{:02d}:{:02d}".format(int(minutes1), int(seconds1))
            self._tmp['RNG'] += f"If there's a critical hit, duration gets a {crit_time_string} increase"
        minutes, seconds = divmod(self._tmp['EffectTime'], 60)
        effect_time_str = "{:02d}:{:02d}".format(int(minutes), int(seconds))

        # hearts
        quarter_heart_map = {
            0: '',
            1: '¼',
            2: '½',
            3: '¾'
        }
        if self._monster_extract_only_health_random_flag or self._monster_extract_health_level_random_flag:
            whole_heart0, quarter_heart0 = divmod(self._tmp['Monster Extract']['HitPointRecover'][0], 4)
            whole_heart0, quarter_heart0 = int(whole_heart0), int(quarter_heart0)
            whole_heart1, quarter_heart1 = divmod(self._tmp['Monster Extract']['HitPointRecover'][1], 4)
            whole_heart1, quarter_heart1 = int(whole_heart1), int(quarter_heart1)
            whole_heart2, quarter_heart2 = divmod(self._tmp['Monster Extract']['HitPointRecover'][2], 4)
            whole_heart2, quarter_heart2 = int(whole_heart2), int(quarter_heart2)
            if effect == 'LifeMaxUp' or self._tmp['Monster Extract']['HitPointRecover'][0] == self.effect['LifeRecover'].get('MaxLv'):
                heart_str0 = '♥'+self._locale_dict['App']['FullRecovery_Name'][self.area_lang]
            else:
                heart_str0 = '♥' * whole_heart0
                if quarter_heart0:
                    heart_str0 += quarter_heart_map[quarter_heart0]+'♥'
            if effect == 'LifeMaxUp' or self._tmp['Monster Extract']['HitPointRecover'][1] == self.effect['LifeRecover'].get('MaxLv'):
                heart_str1 = '♥'+self._locale_dict['App']['FullRecovery_Name'][self.area_lang]
            else:
                heart_str1 = '♥' * whole_heart1
                if quarter_heart1:
                    heart_str1 += quarter_heart_map[quarter_heart1]+'♥'
            if effect == 'LifeMaxUp' or self._tmp['Monster Extract']['HitPointRecover'][2] == self.effect['LifeRecover'].get('MaxLv'):
                heart_str2 = '♥'+self._locale_dict['App']['FullRecovery_Name'][self.area_lang]
            else:
                heart_str2 = '♥' * whole_heart2
                if quarter_heart2:
                    heart_str2 += quarter_heart_map[quarter_heart2]+'♥'
            heart_str0 = "None" if heart_str0 == "" else heart_str0
            heart_str1 = "None" if heart_str1 == "" else heart_str1
            heart_str2 = "None" if heart_str2 == "" else heart_str2
            if self._monster_extract_only_health_random_flag or self._monster_extract_health_level_random_flag:
                self._tmp['RNG'] += f"Monster Extract sets health recovery to {heart_str0}, either health recovery gets 3 additional hearts"
        elif self._critical_only_health_flag or self._critical_health_level_flag or self._critical_health_level_time_flag or self._critical_health_time_flag:
            whole_heart0, quarter_heart0 = divmod(self._tmp['Critical']['HitPointRecover'][0], 4)
            whole_heart0, quarter_heart0 = int(whole_heart0), int(quarter_heart0)
            whole_heart1, quarter_heart1 = divmod(self._tmp['Critical']['HitPointRecover'][1], 4)
            whole_heart1, quarter_heart1 = int(whole_heart1), int(quarter_heart1)
            if effect == 'LifeMaxUp' or self._tmp['Critical']['HitPointRecover'][0] == self.effect['LifeRecover'].get('MaxLv'):
                heart_str0 = '♥'+self._locale_dict['App']['FullRecovery_Name'][self.area_lang]
            else:
                heart_str0 = '♥' * whole_heart0
                if quarter_heart0:
                    heart_str0 += quarter_heart_map[quarter_heart0]+'♥'
            if effect == 'LifeMaxUp' or self._tmp['Critical']['HitPointRecover'][1] == self.effect['LifeRecover'].get('MaxLv'):
                heart_str1 = '♥'+self._locale_dict['App']['FullRecovery_Name'][self.area_lang]
            else:
                heart_str1 = '♥' * whole_heart1
                if quarter_heart1:
                    heart_str1 += quarter_heart_map[quarter_heart1]+'♥'
            heart_str0 = "None" if heart_str0 == "" else heart_str0
            heart_str1 = "None" if heart_str1 == "" else heart_str1
            if self._critical_only_health_flag or self._critical_health_level_flag or self._critical_health_level_time_flag:
                self._tmp['RNG'] += f"If there's a critical hit, health recovery gets 3 additional hearts"
        whole_heart, quarter_heart = divmod(self._tmp['HitPointRecover'], 4)
        whole_heart, quarter_heart = int(whole_heart), int(quarter_heart)
        if effect == 'LifeMaxUp' or self._tmp['HitPointRecover'] == self.effect['LifeRecover'].get('MaxLv'):
            heart_str = '♥'+self._locale_dict['App']['FullRecovery_Name'][self.area_lang]
        else:
            heart_str = '♥' * whole_heart 
            if quarter_heart:
                heart_str += quarter_heart_map[quarter_heart]+'♥'
        heart_str = "None" if heart_str == "" else heart_str

        # level

        if self._monster_extract_only_level_flag or self._monster_extract_health_level_random_flag:
            self._tmp['RNG'] += f'Monster Extract sets effect level to {self._tmp['Monster Extract']['EffectLevel'][0]}, either effect level gets {self._tmp['Monster Extract']['EffectLevel'][2] - self._tmp['Monster Extract']['EffectLevel'][2]} additional level(s)'
        elif self._critical_only_level_flag or self._critical_health_level_flag or self._critical_health_level_time_flag:
            self._tmp['RNG'] += f"If there's a critical hit, effect level gets {self._tmp['Critical']['EffectLevel'][1] - self._tmp['Critical']['EffectLevel'][0]} additional level(s)"
        level_str = str(self._tmp['EffectLevel'])

        # desc

        locale_actor_caption = self._locale_dict['Meal'][f'{result_actor_name}_Caption'][self.area_lang]
        locale_effect_desc = ''
        if effect:
            effect_desc_key = effect
            if result_actor_name == 'Item_Cook_C_17':
                effect_desc_key += '_MedicineDesc'
            else:
                effect_desc_key += '_Desc'
            
            if self.effect[effect].get('MaxLv') <= 3 and self._tmp['EffectLevel'] > 1:
                effect_desc_key += '_{:02d}'.format(self._tmp['EffectLevel'])
            locale_effect_desc = self._locale_dict['Effect'][effect_desc_key][self.area_lang]

        local_meal_desc = (locale_effect_desc +'\n' + locale_actor_caption).strip()
        
        # result

        self._result = {
            'Meal name': locale_meal_name,
            'Actor name': self._tmp['Recipe']['ResultActorName'],
            'Recipe number': self._tmp['Recipe']['PictureBookNum'],
            'Health recovery': heart_str,
            'Effect': locale_buff_name,
            'Effect duration': effect_time_str,
            'Effect level': level_str,
            'Critical rate': str(min(self._tmp['SuperSuccessRate'], 100)) + "%",
            'Sell price': str(self._tmp['SellingPrice']) + " Rupees",
            'Description': local_meal_desc.replace('\n', ' '),
        }

        if self._result['Effect'] == "None":
            self._result['Effect duration'] = "None"
            self._result['Effect level'] = "None"
        elif self._result['Effect'] in ['Extra Hearts', 'Stamina Recovery', 'Extra Stamina', 'Gloom Recovery']:
            self._result['Effect duration'] = "None"

        if self._tmp['RNG']:
            if "If there's a critical hit, " in self._tmp['RNG']:
                crit_text = "If there's a critical hit, "
                part_amount = self._tmp['RNG'].count("If there's a critical hit, ")
                if part_amount == 1:
                    crit_text += self._tmp['RNG'].split("If there's a critical hit, ")[1]
                elif part_amount == 2:
                    crit_text += "either " + self._tmp['RNG'].split("If there's a critical hit, ")[1] + ", either " + self._tmp['RNG'].split("If there's a critical hit, ")[2]
                else:
                    crit_text += "either " + self._tmp['RNG'].split("If there's a critical hit, ")[1] + ", either " + self._tmp['RNG'].split("If there's a critical hit, ")[2]+ ", either " + self._tmp['RNG'].split("If there's a critical hit, ")[3]
                self._result['RNG'] = crit_text
            else:
                me_text = "Monster Extract "
                part_amount = self._tmp['RNG'].count("Monster Extract ")
                if part_amount == 1:
                    me_text += self._tmp['RNG'].split('Monster Extract ')[1]
                elif part_amount == 2:
                    me_text += self._tmp['RNG'].split('Monster Extract ')[1] + " and " + self._tmp['RNG'].split('Monster Extract ')[2]
                else:
                    me_text += self._tmp['RNG'].split('Monster Extract ')[1] + " and, either " + self._tmp['RNG'].split('Monster Extract ')[2] + ", either " + self._tmp['RNG'].split('Monster Extract ')[3]
                self._result['RNG'] = me_text

        # Item_Cook_C_17
        if result_actor_name == 'Item_Cook_C_17':
            self._result['Actor name'] += '_' + self._tmp['Effect']
            self._result['Recipe number'] = self.recipe_card_table.index(self._result['Actor name']) + 1

        self.output = {}
        for k, v in self._result.items():
            self.output[k] = v
        
if __name__ == "__main__":
    meal = TotKCookSim()
    output = meal.cook(["Hearty Truffle"])
    print(output)