"""The resume page. Every fact comes from Andrew's own resume (the image on /resume) and his site; nothing is added.
Emphasis is on directing artists, licensed IP and print production, in his own wording rather than a job posting's."""
from pagekit import esc

FIT = [
 ('Directing artists',
  'Four years directing other artists at Laguna College of Art + Design. I write the briefs (scope, objectives, visual requirements, deliverables, evaluation criteria), review every round, and give feedback as critiques, drawovers and paintovers the artist can act on.',
  '', '../direction/', 'Briefs, redlines and paintovers'),
 ('Licensed IP',
  'Shipped art inside Marvel, Halo, Borderlands (Tiny Tina\u2019s Wonderlands) and Back 4 Blood, working from client briefs and franchise style guides. 160+ character paintings for Marvel Puzzle Quest and card art for Back 4 Blood.',
  '', '../process/', 'Reference to final on Marvel Puzzle Quest'),
 ('Cinematic backgrounds',
  '850+ background paintings for television and feature animation at Titmouse, matching four production styles. Environment color keys and lighting options presented for art director review.',
  '', '../process/comps/', 'Color comps'),
 ('Print production',
  'I own and operate a Canon imagePROGRAF PRO-2000. For Circles of Sin, my original series of 19 paintings, I managed color, prepared print-ready files, ran quality control and sold the prints at Anime Expo, WonderCon, DesignerCon and L.A. Comic Con.', '', '', ''),
]

JOBS = [
 ('Laguna College of Art + Design', 'Adjunct Instructor, Entertainment Design and Game Art', 'Aug 2022 to present', 'Laguna Beach, CA', [
   'Write detailed art briefs defining scope, objectives, visual requirements, deliverables and evaluation criteria for undergraduate courses in character design, environment design and sketching.',
   'Direct visual storytelling, character and environment design, composition, lighting, color and perspective through critiques, paintovers and drawovers that translate creative goals into actionable revisions.',
   'Environment Design 2: wrote an 11 page project brief around a shared world pitch, acted as producer for three teams, set weekly milestones, and reviewed each team against the style guide it built.',
   'Since Fall 2026, provide one on one independent study mentorship.']),
 ('Broken Circle Studios', 'Illustrator, Marvel Puzzle Quest', 'May 2022 to Dec 2025', 'Remote. Licensed mobile live service game for 505 Games and Marvel. Art direction: Amber Ansdell', [
   'Produced 160+ paintings for 32 Marvel characters, with a core set of one hero, three ability and one attack painting per character, plus select ability icons, UI icons and environment paintings.',
   'Worked each character from comic and costume reference through sketches, clean line, color flats and render rounds, revising from art director notes at every stage.',
   'Preserved Marvel character identity and mobile readability across recurring releases.',
   'Delivered all 32 character sets as organized, animation ready PSDs with separated element folders and masks for downstream animators.']),
 ('Titmouse', 'Background Painter', 'Jan 2021 to Aug 2024', 'Four episodic and feature animation productions', [
   'Completed 850+ production paintings: Pantheon (179), Digman! seasons 1 and 2 (277), Metalocalypse: Army of the Doomstar (82) and The Second Best Hospital in the Galaxy (315).',
   'Matched four distinct production styles and integrated art director and supervisor notes.',
   'Created select environment color keys, primarily for Digman! and The Second Best Hospital in the Galaxy.',
   'Built a Blender 3D plane used in Metalocalypse: Army of the Doomstar. Delivered organized, animation ready PSDs.']),
 ('Liquid Development', 'Concept Artist, project contract', 'Jan 2021 to May 2021', 'Tiny Tina’s Wonderlands, Halo: The Master Chief Collection, Back 4 Blood', [
   'Created card art for Back 4 Blood, UI icons for Tiny Tina’s Wonderlands and 10 individual armor pieces for Halo: The Master Chief Collection.',
   'Translated client briefs and franchise style guides into research, thumbnails, revisions and polished Photoshop handoffs, refining composition, lighting, materials, readability and IP fidelity through client reviews.']),
 ('Circles of Sin', 'Creator, Illustrator and Print Producer', '2017 to 2020', 'Original seven part art series. Prints exhibited and sold at Anime Expo, WonderCon, DesignerCon and L.A. Comic Con', [
   'Created 19 paintings plus sketches for a cohesive series interpreting the seven sins through recurring visual language, character design and worldbuilding.',
   'Own and operate a Canon imagePROGRAF PRO-2000: color management, print-ready files, quality control and in-house fine art prints for online and convention sales.']),
]

def resume_body(img, gallery):
    b = ("<div class='cv'><h1>Andrew Dat Tran</h1><p class='lede'>Illustrator, concept artist, background painter and educator. Aliso Viejo, CA.</p>"
         "<p class='note'>(949) 690-4546 &nbsp;·&nbsp; tranandrew16@gmail.com &nbsp;·&nbsp; andrewtranart.com &nbsp;·&nbsp; linkedin.com/in/andrew-d-tran</p>"
         "<h2>Summary</h2><p>Illustrator with 1,000+ finished production paintings across licensed games and animation, and four years of directing other artists’ work. "
         "On Marvel Puzzle Quest I painted 32 Marvel characters, five paintings each, inside a partner’s rules. At Titmouse I matched the look of four different productions. "
         "At Laguna College of Art + Design I write the briefs, set the milestones and give the redlines. I print my own work, so I know what a file needs before it goes to press.</p>"
         "<h2>What I do</h2><div class='fit'>")
    for want, have, extra, href, link in FIT:
        b += f"<div><b>{esc(want)}</b><p>{esc(have)}{' ' + esc(extra) if extra else ''}</p>" + (f"<a href='{href}'>{esc(link)}</a>" if href else '') + "</div>"
    b += "</div><h2>Experience</h2>"
    for org, role, dates, sub, bullets in JOBS:
        b += f"<div class='job'><div class='jh'><b>{esc(org)}</b><span>{esc(dates)}</span></div><p class='role'>{esc(role)}</p><p class='note'>{esc(sub)}</p><ul>" + ''.join(f"<li>{esc(x)}</li>" for x in bullets) + "</ul></div>"
    b += ("<h2>Education</h2><p>Laguna College of Art + Design. BFA, Entertainment Design. Summa cum laude.</p>"
          "<h2>Tools</h2><p>Adobe Photoshop, Procreate, Adobe Illustrator, Blender, Daz3D, ZBrush, Unreal Engine, Adobe Substance 3D Modeler, Adobe Substance 3D Stager.</p>"
          "<h2>Interests</h2><p>Magic: The Gathering. Legends of Runeterra (Top 200 in 2022). VR sculpting. Traditional painting and printmaking. NBA and fantasy basketball.</p>"
          "<h2>Original resume</h2>" + gallery([dict(img, cap='Resume, one page')]) + "</div>")
    return b
