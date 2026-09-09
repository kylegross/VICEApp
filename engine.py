"""Independent survival simulation. All participants join voluntarily."""
import random
from dataclasses import dataclass, field

DUELS = [
    "{a} and {b} duel on roller skates. {a} brakes; {b} discovers the fatal lack of a balcony railing.",
    "{a} lures {b} onto the karaoke stage and drops the lighting rig. {b}'s final number brings the house down.",
    "{b} steals {a}'s satin sheets. {a} wins the resulting duel and adds a ghost to the guest list.",
    "{a} fires a glitter cannon at {b}, who stumbles into the lava lounge. A sparkling fatality.",
    "{a} and {b} joust with beach umbrellas. {a} stays seated; {b} leaves the arena permanently.",
    "{b} challenges {a} to wrestle on a glass table. {a} wins. The table and {b} retire forever.",
    "{a} launches a room-service trolley at {b}. The tip is included; survival is not.",
    "{a} duels {b} on the rooftop infinity pool. {b} discovers exactly where infinity ends.",
    "{b} tries to bribe {a} with a back massage. {a} chooses victory. {b} dies with unused loyalty points.",
    "{a} turns the speed-dating wheel into a spinning arena weapon. {b}'s final date ends abruptly.",
    "{a} defeats {b} in the perfume aisle. The new fragrance is called Eau de Elimination.",
    "{b} hides behind a cardboard cutout of {a}. The real {a} is unimpressed and wins the fatal duel.",
    "{a} severs the rope on {b}'s aerial silk during their duel. {b} makes a fatal unscheduled landing.",
    "{a} and {b} fight over the penthouse key. {a} keeps the key; {b} becomes the penthouse haunting.",
    "{b} attempts a slow-motion charge at {a}. Real-time combat proves fatal for {b}.",
    "{a} tricks {b} into fencing with a breadstick. {b} dies before the main course.",
    "{a} releases a swarm of enchanted roses at {b}. The bouquet delivers a fatal rejection.",
    "{b} signs up for {a}'s private combat lesson. The final exam is fatal, and refunds are unavailable.",
    "{a} knocks {b} into the cursed photo booth. The last strip of pictures shows a newly minted ghost.",
    "{a} wins a duel against {b} using a trophy stolen from the kissing contest. A fatal consolation prize.",
    "{b} throws a dramatic drink in {a}'s face. {a} throws the entire bar back. {b} dies.",
    "{a} and {b} settle a love triangle in the arena. {a} survives; the triangle loses a corner.",
    "{a} defeats {b} beneath a shower of rose petals. The romance is staged, but the elimination is permanent.",
    "{a} challenges {b} to a dance-off on a collapsing balcony. {a} knows when to leave the floor. {b} dies.",
    "{a} catapults a champagne cork across the arena. {b}'s dramatic entrance becomes a dramatic exit.",
    "{b} steals {a}'s date-night dessert. {a} invokes trial by combat. {b} loses more than their reservation.",
    "{a} invites {b} to a private cabana, then activates the ejector seat. {b} leaves the game at impressive speed.",
    "{b} throws a silk robe over {a}'s head. {a} fights blind and still wins. {b} dies of poor tactical planning.",
    "{a} defeats {b} in a duel over who gets the last poolside lounger. The seating chart has an opening.",
    "{a} sends {b} a flirty note attached to a bowling ball. The delivery proves fatal.",
    "{b} pauses mid-fight to fix their hair. {a} respects the look, but finishes the duel. {b} dies fabulous.",
    "{a} weaponizes a confetti cannon. {b}'s last moments are extremely festive.",
    "{a} swaps {b}'s escape boat for an inflatable flamingo. The arena crocodiles appreciate the presentation. {b} dies.",
    "{b} demands a romantic duel at sunrise. {a} arrives early with a trebuchet. {b} never sees breakfast.",
    "{a} catches {b} stealing their signature perfume. One fatal duel later, the scent is officially exclusive.",
    "{a} launches {b} off the mechanical bull with a suspiciously well-timed button press. {b} dies airborne.",
    "{b} tries to disarm {a} with bedroom eyes. {a} counters with actual arena skills. {b} is eliminated permanently.",
    "{a} wins a battle fought entirely with oversized cocktail umbrellas. {b} receives a tiny umbrella on their memorial.",
    "{a} challenges {b} to a midnight rooftop tango. One competitive dip sends {b} out of the game forever.",
    "{b} brings a feather boa to a sword fight. {a} wins, and the arena gains a very stylish ghost.",
    "{a} traps {b} inside a rolling champagne barrel and sends it down the grand staircase. A fatal vintage.",
    "{a} and {b} duel behind the velvet curtain. {a} returns with the curtain, the victory, and no explanation.",
    "{a} defeats {b} with a flying pool noodle reinforced by arena magic. {b}'s final review is one star.",
    "{a} distracts {b} with a scandalous wink, then wins the duel. {b} dies.",
    "{a} and {b} fight over the honeymoon suite. {a} wins; {b} checks out permanently.",
    "{b} challenges {a} to a pillow fight. Unfortunately, {a} brought arena equipment. {b} dies.",
    "{a} exposes {b}'s secret alliance during a candlelit dinner. The resulting duel kills {b}.",
    "{b} tries a seductive entrance. {a} uses the dramatic pause to strike. {b} dies.",
    "{a} steals the last silk robe. {b} demands satisfaction, loses the duel, and dies.",
    "{a} and {b} settle their romantic rivalry with swords. {b} does not survive.",
    "{b} mistakes {a}'s battle stance for flirting. A fatal misunderstanding.",
]
ACCIDENTS = [
    "{b} opens a love letter sealed with a curse. The signature reads 'Your final mistake'. An unexpected death!",
    "{b} leaps into a pile of decorative pillows hiding a portal to the underworld. Permanently checked out.",
    "{b} mistakes the arena's lava lamp for a giant hot tub. The fatal misunderstanding lights up the room.",
    "{b} tries to steal the moonlit gondola. Its enchanted oar rows directly into the afterlife.",
    "{b} orders extra fireworks for a romantic entrance. The entrance becomes a fatal grand finale.",
    "{b} poses beneath the neon 'HOT' sign just as it falls. Their last photo is painfully on-brand.",
    "{b} tests a suspicious massage chair. It folds into a suitcase with fatal efficiency.",
    "{b} blows a kiss at a gargoyle. The gargoyle swoons, falls, and crushes them. An unexpected death!",
    "{b} challenges a cursed mirror to rate their outfit. It awards a perfect ten and a fatal hex.",
    "{b} climbs into a giant gift box to surprise a crush. The box is shipped to the sun. {b} dies in transit.",
    "{b} attempts to crowd-surf at an empty concert. The orchestra pit claims a fatal encore.",
    "{b} follows romantic music into the elevator. The elevator has no floor. An unexpected death!",
    "{b} steals Cupid's bow and accidentally awakens its guardian. A fatal violation of the equipment policy.",
    "{b} ignores the 'Beware of Swan' sign at the lovers' lake. The enormous enchanted swan proves fatal.",
    "{b} tries on a cursed engagement ring. It immediately marries them to the afterlife.",
    "{b} swings from the velvet drapes and knocks loose a stone cherub. A fatal encounter with interior design.",
    "{b} presses 'Extra Hot' on the enchanted sauna. The machine interprets it astronomically. {b} dies.",
    "{b} takes the secret tunnel to the afterparty. Unfortunately, it is an afterlife party. An unexpected death!",
    "{b} leans against the giant wedding cake. Its stone topper falls, ending their dessert plans permanently.",
    "{b} tries to tame a mechanical peacock for a glamorous entrance. A fatal launch follows.",
    "{b} uncorks a bottle containing a very angry genie. Their first wish becomes their last words.",
    "{b} steps onto a rotating bed in the haunted showroom. It spins straight through a portal to oblivion.",
    "{b} accepts a complimentary spa wrap from a mummy. The treatment comes with a fatal ancient curse.",
    "{b} poses on the ice sculpture for a thirst trap. The sculpture collapses. Their final post is chilling.",
    "{b} enters the foam party and discovers the floor is a trapdoor. An unexpected death with excellent bubbles.",
    "{b} mistakes a sleeping dragon for a heated chaise lounge. The booking ends fatally.",
    "{b} opens the minibar marked 'Do not tempt fate'. Fate charges a fatal service fee.",
    "{b} attempts a dramatic robe reveal beside an industrial fan. The arena records a fatal wardrobe malfunction.",
    "{b} flirts with the haunted suit of armor. It takes 'sweep me off my feet' far too literally. {b} dies.",
    "{b} climbs the giant martini glass for a better selfie. The glass tips into the arena abyss. An unexpected death!",
    "{b} wins a lifetime supply of champagne. It arrives all at once. Their lifetime ends under the delivery.",
    "{b} follows a sign promising 'Singles in your area'. It leads to a fatal pit of single spikes.",
    "{b} sits on the throne labeled 'Drama Queen'. The throne launches itself into orbit. {b} does not return alive.",
    "{b} pulls the emergency cord to summon room service. A grand piano arrives instead. An unexpected death!",
    "{b} tries to ride the chocolate fountain. The machinery has a strict no-passengers policy. A fatal dessert disaster.",
    "{b} auditions for the arena's magic show and volunteers for the disappearing act. The magician cannot reverse the fatal spell.",
    "{b} discovers a cursed dating app. Swiping right summons a fatal lightning bolt. Terrible chemistry.",
    "{b} kisses an enchanted frog. It turns into a falling anvil. Fairy tales claim another victim.",
    "{b} argues with a fortune-telling machine. It predicts a falling disco ball with unfortunate accuracy. {b} dies.",
    "{b} lights every candle in the romantic suite. The wax golem awakens and ends the evening fatally.",
    "{b} takes a shortcut through the VIP revolving door. It revolves into another dimension. The arena declares them dead.",
    "{b} orders the house special without reading the menu. The house falls on them. An unexpected death!",
    "{b} performs a victory strut before the game is over and slips into the bottomless hot tub. A fatal premature celebration.",
    "{b} attempts a sultry dance on a chandelier. The ceiling objects. An unexpected death!",
    "{b} follows a trail of rose petals straight into a trapdoor. An unexpected death!",
    "{b} opens a mysterious box labeled 'For a good time'. It explodes. An unexpected death!",
    "{b} leans in to kiss their reflection in a cursed mirror. An unexpected death!",
    "{b} tries to sneak into the VIP hot tub and falls into the arena moat. An unexpected death!",
    "{b} pulls the wrong rope while unveiling a boudoir portrait. A falling piano ends the reveal.",
]
QUIET = [
    "{a} checks the mirror. Still alive, still dangerously overdressed.",
    "{a} requests a cocktail with extra confidence and absolutely no consequences.",
    "{a} flirts with the security camera. Someone has to entertain production.",
    "{a} claims the penthouse by putting a towel on the bed.",
    "{a} rehearses a winner's speech that is mostly thank-yous to good lighting.",
    "{a} changes outfits mid-crisis. The dress code is survival chic.",
    "{a} starts a rumor that the next round includes complimentary massages.",
    "{a} finds a mint on their pillow and treats it as a strategic advantage.",
    "{a} sends a wink across the arena. Nobody knows whether it is flirting or a threat.",
    "{a} negotiates an alliance using nothing but eyebrow movements.",
    "{a} takes a poolside selfie captioned 'unbothered'. They are visibly bothered.",
    "{a} asks room service whether emotional support fries are available.",
    "{a} dramatically fans themselves with the arena rulebook.",
    "{a} discovers the minibar and suddenly believes in second chances.",
    "{a} practices walking away from explosions. There are no explosions, just commitment.",
    "{a} declares a personal intermission to reapply lip balm.",
    "{a} tries to look mysterious behind sunglasses they cannot see through.",
    "{a} rates the arena five stars for atmosphere and one star for hospitality.",
    "{a} finds a feather boa and immediately promotes themselves to management.",
    "{a} asks the moon for romantic advice. The moon wisely stays silent.",
    "{a} orders a breakfast-in-bed tray and uses it as a shield.",
    "{a} leaves a flirty voicemail for destiny. Destiny's inbox is full.",
    "{a} starts a dance break that nobody requested but everyone needed.",
    "{a} steals the decorative cherries from every cocktail in reach.",
    "{a} names their imaginary alliance 'Benefits Pending'.",
    "{a} pretends the arena is a dating show and asks where the confession booth is.",
    "{a} finds silk slippers and becomes impossible to intimidate.",
    "{a} insists their survival strategy is classified. It is mostly hiding.",
    "{a} writes 'Do Not Disturb' on a napkin and wears it as a badge.",
    "{a} sends an air kiss to the audience and invoices them for the experience.",
    "{a} tests the acoustics with a dramatic sigh. Excellent results.",
    "{a} claims their disheveled hair is a deliberate editorial choice.",
    "{a} attempts a sultry lean against a wall, then checks whether anyone saw the wobble.",
    "{a} makes a toast to questionable decisions and surprisingly good cardio.",
    "{a} builds a pillow fort and calls it an exclusive members' lounge.",
    "{a} bargains with a vending machine like it owes them a romantic apology.",
    "{a} schedules a dramatic entrance for a room they are already standing in.",
    "{a} pockets a tiny hotel shampoo. Victory comes in many sizes.",
    "{a} invents a signature pose called 'Still Here, Still Hot'.",
    "{a} asks for a velvet rope around their personal space.",
    "{a} blames their racing heartbeat on chemistry rather than the obvious danger.",
    "{a} turns a beach towel into a cape. The confidence boost is immediate.",
    "{a} reads a fortune cookie: 'Avoid drama.' They request a replacement.",
    "{a} practices a slow-motion hair flip while the rest of the arena waits.",
    "{a} announces that surviving counts as their workout for the entire month.",
    "{a} takes inventory: one robe, two snacks, and wildly misplaced confidence.",
    "{a} starts a guest list for the victory party and puts themselves down twice.",
    "{a} asks whether the arena offers late checkout for attractive survivors.",
    "{a} discovers a karaoke microphone and briefly becomes everyone's biggest concern.",
    "{a} straightens their imaginary crown. The audacity remains undefeated.",
    "{a} practices a devastating pickup line. The furniture remains unimpressed.",
    "{a} discovers a silk robe and makes survival everyone else's second priority.",
    "{a} writes a love letter, then eats it to destroy the evidence.",
    "{a} finds the honeymoon suite and barricades it. Privacy is a strategy.",
    "{a} spends the intermission flirting with a suspiciously handsome statue.",
    "{a} wins a staring contest with their reflection. Confidence restored.",
]

@dataclass
class Game:
    players: list[int]
    rng: random.Random = field(default_factory=random.Random)
    alive: list[int] = field(init=False)
    deaths: list[int] = field(default_factory=list)
    unexpected: list[int] = field(default_factory=list)
    kills: dict[int, int] = field(init=False)
    round: int = 0
    events: list[dict] = field(default_factory=list)

    def __post_init__(self):
        if not 2 <= len(self.players) <= 80 or len(set(self.players)) != len(self.players):
            raise ValueError('A game needs 2–80 unique players.')
        self.alive = self.players.copy()
        self.kills = dict.fromkeys(self.players, 0)

    def step(self):
        self.events = []
        if len(self.alive) <= 1:
            return []
        self.round += 1
        lines = []
        # Every round eliminates at least one player, and always leaves a winner.
        count = min(len(self.alive) - 1, max(1, len(self.alive) // 4))
        for _ in range(count):
            a, b = self.rng.sample(self.alive, 2)
            if self.rng.random() < .28:
                kind = 'unexpected'
                template = self.rng.choice(ACCIDENTS)
                self.unexpected.append(b)
            else:
                kind = 'battle'
                template = self.rng.choice(DUELS)
                self.kills[a] += 1
            lines.append(template.format(a=f'<@{a}>', b=f'<@{b}>'))
            self.events.append({'kind': kind, 'winner': a if kind == 'battle' else None,
                                'eliminated': b, 'text': lines[-1]})
            self.alive.remove(b)
            self.deaths.append(b)
        if len(self.alive) > 1:
            lines.append(self.rng.choice(QUIET).format(a=f'<@{self.rng.choice(self.alive)}>'))
        return lines

    def awards(self):
        if len(self.alive) != 1:
            raise ValueError('The game is not over.')
        best = max(self.kills.values())
        return {
            'Winner': self.alive.copy(),
            'First death': self.deaths[:1],
            'Unexpected deaths': self.unexpected.copy(),
            f'Most eliminations ({best})': [p for p in self.players if self.kills[p] == best] if best else [],
            'Runner-up': self.deaths[-1:],
            'Survived without a kill': [self.alive[0]] if self.kills[self.alive[0]] == 0 else [],
        }
