"""Static analysis figures; every plotted mark has a CSV row."""
import csv
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

COLORS=['#72767D','#BD8A2E','#2563A6']
MARKERS=['s','^','o']
YEARS=['2024','2025','2026']
NAMES={
 'answering_model':'Answering models','agent_or_tool_system':'Agents / tool systems','embodied_system':'Embodied systems',
 'general_or_cross_domain':'General / cross-domain','language_and_communication':'Language / communication',
 'mathematics_and_formal_reasoning':'Mathematics / formal reasoning','software_and_coding':'Software / coding',
 'natural_sciences':'Natural sciences','engineering':'Engineering','healthcare_biomedicine':'Healthcare / biomedicine',
 'law_and_public_policy':'Law / public policy','finance_and_business':'Finance / business','cybersecurity':'Cybersecurity',
 'education':'Education','social_sciences_and_humanities':'Social sciences / humanities','other':'Other',
 'fixed_items':'Fixed items','runtime_generated_items':'Runtime-generated items','interactive_loop':'Interactive loop',
 'human_or_real_world':'Human / real-world','program_or_simulation':'Program / simulation','generative_model':'Generative model',
 'reference_or_metric':'Reference / metric','execution_or_environment':'Execution / environment',
 'llm_judge':'LLM judge','other_model_judge':'Other model judge','human_judge':'Human judge',
 'not_reported':'Not reported','unclear':'Unclear','structured_data':'Structured data'}


def save(fig,out,name,rows):
    from run import csvwrite
    for ext in ['png','svg']:
        fig.savefig(out/'figures'/f'{name}.{ext}',dpi=180,facecolor='white',bbox_inches='tight',metadata={'Date':None} if ext=='svg' else None)
    csvwrite(out/'figures'/f'{name}_data.csv',rows)
    plt.close(fig)


def dots(ax,rows,field,title):
    values=[r for r in rows if r['window']=='jan_aug' and r['year'] in YEARS and r['field']==field]
    labels=sorted({r['label'] for r in values},key=lambda t:-sum(r['n'] for r in values if r['label']==t))
    y=np.arange(len(labels))
    for i,year in enumerate(YEARS):
        lookup={r['label']:r for r in values if r['year']==year}
        rates=[lookup[t]['share']*100 for t in labels]
        ax.scatter(rates,y+(i-1)*0.18,label=year,color=COLORS[i],marker=MARKERS[i],s=35,zorder=3)
    ax.set_yticks(y,[NAMES.get(t,t.replace('_',' ').capitalize()) for t in labels])
    ax.invert_yaxis()
    ax.set_xlim(0,100)
    ax.set_xlabel('Share of field-valid paper records (%)')
    ax.set_title(title,loc='left',pad=14)
    ax.grid(axis='x',color='#dddddd',linewidth=.6)
    ax.set_axisbelow(True)
    for s in ['top','right']: ax.spines[s].set_visible(False)
    ax.legend(frameon=False,loc='lower right',fontsize=8)
    return values


def headers(fig,title,subtitle,footer):
    fig.suptitle(title,x=.02,ha='left',fontsize=15,fontweight='bold',y=.99)
    fig.text(.02,.944,subtitle,fontsize=9,ha='left')
    fig.text(.02,.012,footer,fontsize=8,ha='left')


def make(out,tables,design,roles,flow,cfg):
    from run import csvwrite,write
    (out/'figures').mkdir()
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.hashsalt':'benchmark-paper-v1','axes.titleweight':'bold'})
    labels,quality,language,strata=tables
    subtitle='First submissions in January-August of each year; model-coded labels; overlapping categories'
    foot='2024 n=1,683; 2025 n=3,284; 2026 n=5,734. Field-valid denominators vary; see data CSV.'
    # Figure 1: text-box flow prevents branch counts being mistaken for proportions.
    fig,ax=plt.subplots(figsize=(11,8));ax.axis('off');ax.set_xlim(0,1);ax.set_ylim(0,1)
    stages=[('Metadata frame',flow['frame_n']),('M0 retained',flow['m0_n']),('Abstract candidates',flow['candidate_n']),
            ('Available full text',flow['source_ready_n']),('Included paper records',14767)]
    notes=[f"M0 not retained: {flow['frame_n']-flow['m0_n']:,}",
           f"Abstract excluded: {flow['metadata_decisions']['excluded_by_metadata']:,}\nUndetermined (not routed): {flow['metadata_decisions']['semantic_unresolved_not_routed']:,}",
           f"Unavailable source: {flow['source_unavailable_n']:,}",
           'Full-text excluded: 1,424\nUnresolved: 185']
    for i,(label,n) in enumerate(stages):
        y=.85-i*.17
        ax.text(.31,y,f'{label}\n{n:,}',ha='center',va='center',bbox=dict(boxstyle='round,pad=.65',fc='#f1f3f5',ec='#444444'),fontsize=12)
        if i<4:
            ax.annotate('',xy=(.31,y-.115),xytext=(.31,y-.055),arrowprops=dict(arrowstyle='->',color='#444444'))
            ax.text(.65,y-.07,notes[i],fontsize=10,va='center')
            ax.annotate('',xy=(.62,y-.07),xytext=(.43,y-.07),arrowprops=dict(arrowstyle='->',color='#72767D'))
    headers(fig,'Study selection and analysis population','January 2022-August 2026 | one exact-version record per paper',
            'Included: 14,736 complete + 31 partially valid label records. Unresolved records are not coded as negative examples.')
    save(fig,out,'fig1_selection',[{'stage':s,'n':n} for s,n in stages]+[{'stage':notes[i].replace('\n','; '),'n':''} for i in range(4)])
    fig,axs=plt.subplots(1,2,figsize=(14,8),gridspec_kw={'width_ratios':[.8,1.3]})
    d=dots(axs[0],labels,'target_system','A. Target systems')+dots(axs[1],labels,'evaluation_domain','B. Evaluation domains')
    headers(fig,'Targets and domains of evaluation',subtitle,foot)
    fig.subplots_adjust(left=.16,right=.98,top=.85,bottom=.10,wspace=.85)
    save(fig,out,'fig2_targets_domains',d)
    fig,axs=plt.subplots(1,3,figsize=(16,6))
    d=[]
    for ax,f,title in zip(axs,['material_origin','evaluation_setup','modality'],['A. Material origin','B. Evaluation setup','C. Modality']):
        d+=dots(ax,labels,f,title)
    headers(fig,'Materials and test conditions',subtitle,foot+' Not reported / unclear do not mean absent.')
    fig.subplots_adjust(left=.13,right=.98,top=.80,bottom=.15,wspace=.85)
    save(fig,out,'fig3_materials_setup',d)
    fig,axs=plt.subplots(1,3,figsize=(16,6),gridspec_kw={'width_ratios':[1.3,1,1]})
    data=dots(axs[0],labels,'scoring_source','A. Scoring mechanisms')
    sub=[r for r in strata if r['window']=='jan_aug' and r['year'] in YEARS and r['group'] in ['agent','non_agent'] and r['label']=='llm_judge']
    for i,year in enumerate(YEARS):
        vals=[next(r['share']*100 for r in sub if r['year']==year and r['group']==g) for g in ['agent','non_agent']]
        axs[1].scatter(vals,np.arange(2)+(i-1)*.14,color=COLORS[i],marker=MARKERS[i],s=40,label=year)
    axs[1].set_yticks([0,1],['Agent','Non-agent']);axs[1].invert_yaxis();axs[1].set_xlim(0,100)
    axs[1].set_xlabel('LLM judge (%)');axs[1].set_title('B. Within target groups',loc='left');axs[1].grid(axis='x',color='#dddddd');axs[1].legend(frameon=False)
    dec=next(d for d in design['decompositions'] if d['cohort']=='primary' and d['outcome']=='llm' and d['strata']==['agent'] and d['start']=='2024')
    v=[dec[k]*100 for k in ['composition','within','delta']]
    bars=axs[2].bar(['Mix','Within','Total'],v,color=[COLORS[1],COLORS[2],COLORS[0]],edgecolor='#333333')
    for bar,value in zip(bars,v):axs[2].text(bar.get_x()+bar.get_width()/2,value+.3,f'{value:.2f}',ha='center',fontsize=9)
    axs[2].set_ylim(0,18);axs[2].set_ylabel('Change (percentage points)');axs[2].set_title('C. 2024 to 2026 allocation',loc='left')
    headers(fig,'Scoring mechanisms and within-group change',subtitle,
            'Panels A/B: field-valid records. C: symmetric arithmetic decomposition by agent status; not causal effects.')
    fig.subplots_adjust(left=.13,right=.98,top=.80,bottom=.17,wspace=.65)
    # All panels use one uniform data-table shape, including units/denominator.
    records=[dict(panel='A',year=r['year'],metric=r['label'],n=r['n'],valid_n=r['valid_n'],value=r['share'],unit='proportion') for r in data]
    records += [dict(panel='B',year=r['year'],metric=r['group'],n=r['n'],valid_n=r['valid_n'],value=r['share'],unit='proportion') for r in sub]
    records += [dict(panel='C',year='2024_to_2026',metric=k,n='',valid_n=json.dumps(dec['valid_n']),value=dec[k]*100,unit='percentage_points') for k in ['composition','within','delta']]
    save(fig,out,'fig4_scoring',records)
    fig,axs=plt.subplots(1,2,figsize=(13,6))
    ass=[r for r in design['material_judge_associations'] if r['cohort']=='primary']
    cats=['neither_n','exposure_only_n','outcome_only_n','both_n']
    names=['Neither tag','Generated only','LLM judge only','Both tags']
    colors=['#dddddd',COLORS[1],COLORS[0],COLORS[2]]
    bottom=np.zeros(3);records=[]
    for key,name,color,hatch in zip(cats,names,colors,['','//','..','xx']):
        values=np.array([next(r for r in ass if r['year']==y)[key]/next(r for r in ass if r['year']==y)['valid_n']*100 for y in YEARS])
        axs[0].bar(YEARS,values,bottom=bottom,color=color,hatch=hatch,label=name,edgecolor='#333333',linewidth=.5)
        for i,y in enumerate(YEARS):
            r=next(r for r in ass if r['year']==y)
            records.append(dict(panel='A',year=y,metric=key,n=r[key],valid_n=r['valid_n'],share=r[key]/r['valid_n']))
        bottom+=values
    axs[0].set_ylim(0,100);axs[0].set_ylabel('Jointly field-valid records (%)');axs[0].set_title('A. Material generation and LLM scoring',loc='left')
    axs[0].legend(frameon=False,fontsize=8,loc='lower center',bbox_to_anchor=(.5,-.25),ncol=2)
    both=roles['generated_and_llm_judge_n'];r=roles['within_llm_intersection']
    vals=[r['human_material_n']/both*100,r['any_additional_scoring_n']/both*100]
    axs[1].barh(['Human / real-world\nmaterials also present','Other scoring\nmechanisms also present'],vals,color=COLORS[2],edgecolor='#333333')
    axs[1].set_xlim(0,100);axs[1].invert_yaxis();axs[1].set_xlabel('Share of intersection (%)');axs[1].set_title('B. Mixed designs within intersection',loc='left')
    for i,v in enumerate(vals):axs[1].text(v+1,i,f'{v:.1f}%',va='center')
    for k in ['human_material_n','any_additional_scoring_n']:records.append(dict(panel='B',year='2022-01_to_2026-08',metric=k,n=r[k],valid_n=both,share=r[k]/both))
    headers(fig,'Model-generated materials and LLM scoring',
            'A: January-August 2024/2025/2026 | B: all 3,272 jointly tagged records across the full study window',
            'Paper-level co-occurrence does not establish the same actor/component or an autonomous evaluation loop. Panel B bars overlap.')
    fig.subplots_adjust(left=.07,right=.98,top=.80,bottom=.22,wspace=.65)
    save(fig,out,'fig5_material_scoring',records)
    write(out/'chart_map.json',{'renderer':'Matplotlib static SVG/PNG','palette':COLORS,
                               'charts':{f'fig{i}':{'question':q,'data':'figures/'+name+'_data.csv','preview':'figures/'+name+'.png'} for i,q,name in [
                                   (1,'Which records reach analysis?','fig1_selection'),(2,'What systems and domains?','fig2_targets_domains'),
                                   (3,'What materials and conditions?','fig3_materials_setup'),(4,'What counts as success and where is scoring changing?','fig4_scoring'),
                                   (5,'How do generation and scoring coexist?','fig5_material_scoring')]}})
