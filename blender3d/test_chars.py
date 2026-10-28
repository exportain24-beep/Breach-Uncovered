# Blender test: build MPFB (MakeHuman) characters, light them, render portraits + a lineup. Run: blender -b -P blender3d/test_chars.py -- OUTDIR ENGINE
import bpy, sys, os, importlib, math, time, json
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "/tmp/out"; ENGINE = argv[1] if len(argv) > 1 else "CYCLES"; HDRI = os.environ.get("HDRI", "")
os.makedirs(OUT, exist_ok=True)
for m in list(bpy.context.preferences.addons.keys()): pass
try: bpy.ops.preferences.addon_enable(module="bl_ext.user_default.mpfb")
except Exception as e: print("addon_enable:", e)
def imp(pkg, key):
    for amod in list(sys.modules):
        if amod.endswith(pkg): return getattr(importlib.import_module(amod), key)
    raise ValueError(pkg)
HS = imp("mpfb.services.humanservice", "HumanService"); AS = imp("mpfb.services.assetservice", "AssetService"); HOP = imp("mpfb.entities.objectproperties", "HumanObjectProperties"); TS = imp("mpfb.services.targetservice", "TargetService")
lists = {}
for sub, typ in (("clothes", "mhclo"), ("hair", "mhclo"), ("skins", "mhmat"), ("eyebrows", "mhclo"), ("eyes", "mhclo"), ("eyelashes", "mhclo")):
    try: AS.update_asset_list(asset_subdir=sub, asset_type=typ); lists[sub] = sorted(v["basename"] for v in AS.get_asset_list(asset_subdir=sub, asset_type=typ).values())
    except Exception as e: lists[sub] = ["ERR " + str(e)]
json.dump(lists, open(os.path.join(OUT, "assets.json"), "w"), indent=1); print({k: len(v) for k, v in lists.items()})
def pick(sub, *names):
    for n in names:
        for b in lists.get(sub, []):
            if n in b: return b
    return None
bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete()
def human(gender, skin, hair, clothes, x, macro=None):
    h = HS.create_human(); h.location = (x, 0, 0)
    HOP.set_value("gender", gender, entity_reference=h)
    for k, v in (macro or {}).items(): HOP.set_value(k, v, entity_reference=h)
    TS.reapply_macro_details(h)
    sp = AS.find_asset_absolute_path(skin, asset_subdir="skins") if skin else None
    if sp: HS.set_character_skin(sp, h, skin_type="MAKESKIN")
    for sub, f, t in (("eyes", pick("eyes", "brown", "low-poly", ""), "Eyes"), ("eyebrows", pick("eyebrows", "eyebrow001", ""), "Eyebrows"), ("eyelashes", pick("eyelashes", "eyelashes01", ""), "Eyelashes"), ("hair", hair, "Hair")) + tuple(("clothes", c, "Clothes") for c in clothes):
        if not f: continue
        p = AS.find_asset_absolute_path(f if f.endswith(".mhclo") else f + ".mhclo", asset_subdir=sub)
        if p:
            try: HS.add_mhclo_asset(p, h, asset_type=t, material_type="MAKESKIN")
            except Exception as e: print("asset fail", f, e)
        else: print("missing", sub, f)
    try:
        rig = HS.add_builtin_rig(h, "default"); 
        for b in rig.pose.bones:
            if b.name.startswith("upperarm01"): b.rotation_mode = "XYZ"; b.rotation_euler = (0, 0, math.radians(-62 if b.name.endswith(".L") else 62))
            if b.name.startswith("lowerarm01"): b.rotation_mode = "XYZ"; b.rotation_euler = (math.radians(-18), 0, 0)
        print("bones:", [b.name for b in rig.pose.bones][:60])
    except Exception as e: print("rig fail", e)
    return h
skin_m = pick("skins", "young_caucasian_male", "male"); skin_f = pick("skins", "young_caucasian_female", "female"); skin_d = pick("skins", "young_african_male", "african", "middleage")
suit_m = pick("clothes", "toigo_male_suit_3", "male_suit", "suit"); suit_f = pick("clothes", "toigo_female_suit", "female_suit")
shoes = pick("clothes", "shoes06", "shoes0", "shoe"); hair_m = pick("hair", "short02", "short", "messy"); hair_f = pick("hair", "toigo_blunt_bob", "bob", "long")
casual = pick("clothes", "male_casualsuit", "casual"); 
print("chosen", skin_m, skin_f, skin_d, suit_m, suit_f, shoes, hair_m, hair_f, casual)
H = [human(0.0, skin_m, hair_m, [suit_m, shoes], -1.6), human(1.0, skin_f, hair_f, [suit_f, shoes], -.55), human(0.0, skin_d, hair_m, [casual, shoes], .55, {"african": 1.0, "caucasian": 0.0}), human(0.0, skin_m, None, [casual, shoes], 1.6, {"age": .8})]
# ---- studio room + lights
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0)); fl = bpy.context.object; m = bpy.data.materials.new("floor"); m.use_nodes = True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (.18, .19, .22, 1); m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = .45; fl.data.materials.append(m)
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 6, 10), rotation=(math.radians(90), 0, 0)); wl = bpy.context.object; m2 = bpy.data.materials.new("wall"); m2.use_nodes = True; m2.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (.06, .12, .25, 1); wl.data.materials.append(m2)
def area(name, loc, rot, energy, size, color):
    bpy.ops.object.light_add(type="AREA", location=loc, rotation=rot); L = bpy.context.object; L.data.energy = energy; L.data.size = size; L.data.color = color; return L
area("key", (-3, -4, 3.5), (math.radians(55), 0, math.radians(-35)), 900, 3, (1, .95, .88)); area("fill", (4, -3, 2), (math.radians(60), 0, math.radians(50)), 250, 4, (.75, .85, 1)); area("rim", (0, 3, 3.5), (math.radians(-60), 0, 0), 700, 3, (.6, .75, 1))
w = bpy.context.scene.world or bpy.data.worlds.new("w"); bpy.context.scene.world = w; w.use_nodes = True
if HDRI and os.path.exists(HDRI):
    nt = w.node_tree; env = nt.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(HDRI); nt.links.new(env.outputs["Color"], nt.nodes["Background"].inputs["Color"]); nt.nodes["Background"].inputs["Strength"].default_value = .35
S = bpy.context.scene; S.render.resolution_x, S.render.resolution_y = 1080, 1920; S.render.image_settings.file_format = "PNG"
if ENGINE == "EEVEE":
    S.render.engine = "BLENDER_EEVEE_NEXT"; S.eevee.taa_render_samples = 32
    try: S.eevee.use_raytracing = True; S.eevee.use_shadows = True
    except Exception: pass
else:
    S.render.engine = "CYCLES"; S.cycles.device = "CPU"; S.cycles.samples = 48; S.cycles.use_denoising = True; S.cycles.denoiser = "OPENIMAGEDENOISE"
bpy.ops.object.camera_add(); cam = bpy.context.object; S.camera = cam; cam.data.lens = 50; cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 2.2
def look(cam, at):
    import mathutils; d = mathutils.Vector(at) - cam.location; cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
shots = [("lineup", (0, -7.5, 1.5), (0, 0, 1.05), 32, 7.0), ("closeup_agentM", (-1.35, -1.25, 1.66), (-1.6, 0, 1.6), 70, 1.3), ("closeup_agentF", (-.4, -1.25, 1.58), (-.55, 0, 1.52), 70, 1.3), ("closeup_man2", (.75, -1.25, 1.62), (.55, 0, 1.58), 70, 1.3)]
times = {}
for name, loc, at, lens, focus in shots:
    cam.location = loc; look(cam, at); cam.data.lens = lens; cam.data.dof.focus_distance = focus
    S.render.filepath = os.path.join(OUT, f"{name}_{ENGINE}.png"); t0 = time.time(); bpy.ops.render.render(write_still=True); times[name] = round(time.time() - t0, 1); print("rendered", name, times[name], flush=True)
json.dump(times, open(os.path.join(OUT, f"times_{ENGINE}.json"), "w"))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "chars_test.blend"))
