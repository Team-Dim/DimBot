import dimsecret
import missile
import coc

clan_tag = '#URU2RY9J'

class Hyperstellar(missile.Cog):

    def __init__(self, bot):
        super().__init__(bot, 'Hyperstellar')
        self.clan_log = None
        self.donated = {}
        self.received = {}
        self.coc = coc.EventsClient()
        self.coc.add_war_updates(clan_tag)
        self.coc.add_clan_updates(clan_tag)

        @self.coc.event
        @coc.ClanEvents.member_donations()
        async def on_member_donation(old: coc.ClanMember, new: coc.ClanMember):
            self.donated[new.name] = new.donations - old.donations

        @self.coc.event
        @coc.ClanEvents.member_received()
        async def on_member_received(old: coc.ClanMember, new: coc.ClanMember):
            self.received[new.name] = new.received - old.received

        @self.coc.event
        @coc.ClientEvents.clan_loop_finish()
        async def on_client_clan_loop_finish(no):
            if self.donated:
                msg = '[DNT]'
                for member, count in self.donated.items():
                    msg += f' {member}: {count}'
                msg += '\n =>'
                for member, count in self.received.items():
                    msg += f' {member}: {count}'
                self.donated.clear()
                self.received.clear()
                await self.clan_log.send(msg)

        @self.coc.event
        @coc.WarEvents.new_war()
        async def on_new_war(war: coc.ClanWar):
            if not war.is_cwl:
                await self.clan_log.send('New War: ' + war.opponent.name)

        @self.coc.event
        @coc.WarEvents.state()
        async def on_war_state(old, new: coc.ClanWar):
            if not new.is_cwl:
                msg = f'<@{self.bot.owner_id}>'+new.state + '\n'
                for member in new.members:
                    if not member.is_opponent and not member.attacks:
                        msg += member.name + ' '
                await self.bot.get_cog('Hamilton').bot_test.send(msg)

        @self.coc.event
        @coc.WarEvents.war_attack()
        async def on_war_atk(atk: coc.WarAttack, war: coc.ClanWar):
            attacker = atk.attacker
            if not attacker.is_opponent and not war.is_cwl:
                name, pos = attacker.name, str(attacker.map_position)
                if attacker.map_position != atk.defender.map_position:
                    pos = missile.underline(pos)
                fresh_attack = '1' if atk.is_fresh_attack else '2'
                atk_s = -war.start_time.seconds_until - atk.duration
                atk_h, atk_s = divmod(atk_s, 3600)
                atk_m, atk_s = divmod(atk_s, 60)
                atk_time = f'{atk_h}h {atk_m}m {atk_s}s'
                if not atk.is_fresh_attack and atk_h < 12:
                    atk_time += ' ⚠Early'
                elif atk.is_fresh_attack and atk_h >= 12:
                    atk_time += ' ⚠Late'
                await self.clan_log.send(f'[ATK] {name} ({pos}) {fresh_attack}⚔️ @{atk_time}')


    @missile.Cog.listener()
    async def on_ready(self):
        self.clan_log = self.bot.get_cog('Hamilton').bot_test if dimsecret.debug else self.bot.get_channel(1099026457268863017)
        await self.coc.login_with_tokens(dimsecret.coc)

