import PIL.Image
import tempfile, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(6,5))
labels = ['Text','Tables','Images','Charts','Math/Code']
sizes  = [45, 20, 15, 12, 8]
palette = ['#4F81BD','#C0504D','#9BBB59','#8064A2','#4BACC6']
ax.pie(sizes, labels=labels, autopct='%1.1f%%',
       startangle=140, colors=palette, explode=[0.05]*5)
ax.set_title('Content-Type Distribution', fontweight='bold')

tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
tmp.close()
fig.savefig(tmp.name, dpi=150, bbox_inches='tight')
plt.close(fig)

img = PIL.Image.open(tmp.name)
print(f'Pie chart actual size: {img.size[0]}x{img.size[1]} px')
print(f'Width 10cm = {10*28.35:.1f}pt')
print(f'Height at 10cm width = {10*28.35 * img.size[1]/img.size[0]:.1f}pt = {10 * img.size[1]/img.size[0]:.2f}cm')
os.unlink(tmp.name)
