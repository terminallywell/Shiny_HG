'''
Seung Suk Lee 081823 update

# Acknowledgment
This research and software development was supported by NSF BCS-2140826 
awarded to the University of Massachusetts Amherst.

Special thanks to Joe Pater, Brandon Prickett.
'''

####################################################
# pkgs
####################################################

# necessary pkgs
from pulp import *
import numpy as np
import pandas as pd
import mpmath
from itertools import product, combinations_with_replacement
from more_itertools import partitions
from collections import defaultdict, Counter
from re import sub, search
from tqdm import tqdm # I had to change `from tqdm.notebook import tqdm` to `from tqdm import tqdm`
from os import listdir, path, mkdir
import pickle
# from google.colab import files
import urllib.request



####################################################
# Reading input file
####################################################

def read_file(filename):
  filename += '.csv'
  myInputFile = pd.read_csv(filename)
  myInputFile = myInputFile.iloc[1:]
  myInputFile = myInputFile.reset_index(drop=True)
  myInputFile[['UR', 'SR']] = myInputFile[['UR', 'SR']].fillna(method='ffill')
  return myInputFile

####################################################
# Gen
####################################################

def gen_URlist(data):
  URlist = np.unique(data.UR).tolist()
  URlist = [x for x in URlist if x != '-']
  return URlist

def gen_SR(data, udl):
  return np.unique(data.loc[data.UR==udl,'SR']).tolist()

def gen_HR(data, sfc):
  return data.loc[data.SR==sfc,'HR'].tolist()

def full_cands(data, udl):
  return data.loc[data.UR==udl,'HR'].tolist()

def convertXtoY(data, x, form, y):
  return data.loc[data[x]==form][y].values[0]

####################################################
# Finding the winners in the input file
####################################################
def get_winners(data):
  return data.loc[data.Obs==1,'SR'].tolist()

####################################################
# CON
####################################################

# individual constraint violation searching fn.

def Con(data, cName, cand):
  if 'HR' in data.columns:
    try:
      return data.loc[data.HR==cand, cName].values[0]
    except KeyError:
      print(f'"{cName}" is not a constraint in your input file')
  else:
    try:
      return data.loc[data.SR==cand, cName].values[0]
    except KeyError:
      print(f'"{cName}" is not a constraint in your input file')

####################################################
# Eval
####################################################

def get_constraint_names(data):
  if 'HR' in data.columns:
    return data.columns[4:].tolist()
  else:
    return data.columns[3:].tolist()

def evaluate_SR(data, cand):
  con_names = get_constraint_names(data)

  if 'HR' in data.columns:
    viol = data.loc[data.HR==cand, con_names].values[0]
    viol = [int(v) for v in viol]
    return np.array(viol)
  else:
    viol = data.loc[data.SR==cand, con_names].values[0]
    viol = [int(v) for v in viol]
    return np.array(viol)

def evaluate_SRs(data, ListOfCands):
  viols = [evaluate_SR(data, cand) for cand in ListOfCands]
  return np.stack(viols)


####################################################
# Learning fns
####################################################

def prepare_data_for_learning(data):
  '''
  ur = unique_underlying (list of all URs in brandonian form)
  sr = unique_surface (list of all SRs in brandonian form)
  cands = ListOfCandidates (list of all candidates in st2 form to be assigned viols)
  data = ListOfSurfaces (list of SRs in the length of HRs (i.e., with repetitions), in brandonian form
      later to be used in gradient descent function)
  ur2datum = underlying2data (dictionary for each UR (brandonian), how many HRs it has, as ranges)
  sr2datum = surface2data (dictionary for each SR (brandonian), how many HRs it has, as ranges)
  '''
  unique_underlying = gen_URlist(data)

  unique_surface = []
  ListOfCandidates = []
  if 'HR' in data.columns:
    for udl in unique_underlying:
      unique_surface.extend(gen_SR(data, udl)) # list of all SR
      ListOfCandidates.extend(full_cands(data, udl)) # list of all HR - Foot
  else:
    for udl in unique_underlying:
      unique_surface.extend(gen_SR(data, udl))
      ListOfCandidates.extend(gen_SR(data, udl))

  # initiate dictionaries {ur:[]} and {sr:[]} in the list of candidates
  underlying2data = {form:[] for form in unique_underlying}
  surface2data = {form:[] for form in unique_surface}

  if 'HR' in data.columns: # list of candidates is unique surface
    for datum_index, form in enumerate(ListOfCandidates):
      underlying2data[convertXtoY(data, 'HR',form,'UR')].append(datum_index)
      surface2data[convertXtoY(data, 'HR',form,'SR')].append(datum_index) # this is for assigning violations
    ListOfSurfaces = [convertXtoY(data, 'HR',form,'SR') for form in ListOfCandidates] # this is later to loop through/SRs in length of HRs
    return unique_underlying, unique_surface, ListOfCandidates, ListOfSurfaces, underlying2data, surface2data

  else: # list of candidates is list of HRs
    for datum_index, form in enumerate(unique_surface):
      underlying2data[convertXtoY(data, 'SR',form,'UR')].append(datum_index)
      surface2data[form].append(datum_index) # this is for assigning violations, each sr has 1 index
    return unique_underlying, unique_surface, ListOfCandidates, unique_surface, underlying2data, surface2data

def get_normalized_probs(winners, surface2data, unique_underlying, data):
  '''
  Note: 'data' is unique_surface (Grid) or ListOfSurfaces (Foot)
  '''
  probs=[]
  for sfc in data:
    if sfc in winners:
      probs.append(1)
    else:
      probs.append(0)
  probs = np.array(probs) # length = Number of HRs

  new_probs = []
  for datum_index, this_prob in enumerate(probs):
    new_prob = this_prob/(len(surface2data[data[datum_index]])*len(unique_underlying))
    # default: 1/NumberOfUR, but also weighted by how many HRs exist for that SR
    new_probs.append(new_prob)
  return np.array(new_probs)

def initialize_weights(constraint_number, init_weight, rand_weights):
  if rand_weights:
    initial_weights = list(np.random.uniform(low=0.0, high=10.0, size=constraint_number))
    #Init constraint weights = rand 1-10
    print("Initial weights: ", initial_weights)
  else:
    initial_weights = [init_weight] * constraint_number
  return initial_weights

def get_predicted_probs(weights, viols, unique_underlying, underlying2data):
  # maybe later check: unique_underlying just ur2datum keys
  harmonies = viols.dot(weights)
  eharmonies = np.exp(harmonies)
  #Calculate denominators to convert eharmonies to predicted probs:
  Zs = np.array([mpmath.mpf(0.0) for z in range(viols.shape[0])])
  for underlying_form in unique_underlying:     #Sum of eharmonies for this UR (converts to probs)
    this_Z = sum(eharmonies[underlying2data[underlying_form]])\
                                    *float(len(unique_underlying)) #Number of UR's (normalizes the updates)
    if this_Z == 0:
      eharmonies = np.array([mpmath.exp(h) for h in harmonies])
      this_Z = sum(eharmonies[underlying2data[underlying_form]])\
                                  *float(len(unique_underlying))
      Zs[underlying2data[underlying_form]] = this_Z
    else:
      Zs[underlying2data[underlying_form]] = mpmath.mpf(this_Z)

  #Calculate prob for each datum:
  probs = []
  for datum_index, eharm in enumerate(eharmonies):
    if Zs[datum_index] == 0:
        #error_f = open("_weights.csv", "w")
        #error_f.write("\n".join([str(w) for w in weights]))
        #error_f.close()
        #print("\n\n"+remember_me+"\n\n")
      raise Exception("Rounding error! (Z=0 for "+unique_underlying[datum_index]+")")
    else:
      probs.append(float(eharm/Zs[datum_index]))

  return np.array(probs)

def check_learning(data, cur_weights):
  '''
  given a weight vector and a list of observed winnerSR for each UR,
  if the weight vector allows the observed winnerSR to have .90 prob,
  return True else False
  '''
  UDLs = gen_URlist(data)
  winners = get_winners(data)

  for i in range(len(UDLs)):
    cur_UR = UDLs[i] # loop through each UR

    if 'HR' in data.columns:
      candidates = full_cands(data, cur_UR)
      surfaces = [convertXtoY(data, 'HR', form, 'SR') for form in candidates]
    else:
      candidates = gen_SR(data, cur_UR)
      surfaces = gen_SR(data, cur_UR)

    winner_ids = []
    cur_winner = winners[i]
    for id, sfc in enumerate(surfaces):
      if sfc==cur_winner:
        winner_ids.append(id)
    if 'HR' in data.columns:
      viol_vec = -1*evaluate_SRs(data, full_cands(data, cur_UR)) #
    else:
      viol_vec = -1*evaluate_SRs(data, gen_SR(data, cur_UR)) #
    harmonies = viol_vec.dot(cur_weights)
    eharmonies = np.exp(harmonies)
    Z = sum(eharmonies)
    probs = eharmonies/Z
    if sum(probs[winner_ids])<.90:
      return False
  return True

def learn_language(data, rand_weights = False, init_weights = 1, neg_weights = False, epochs = 10, eta=4.):
  myConNames = get_constraint_names(data)
  CON_num = len(myConNames)

  ur, sr, cands, DATA, ur2datum, sr2datum = prepare_data_for_learning(data)
  v = evaluate_SRs(data, cands) * -1
  weights = initialize_weights(CON_num, init_weights, rand_weights)

  cur_winners = get_winners(data)
  td_probs = get_normalized_probs(cur_winners, sr2datum, ur, DATA)

  if epochs==0:
    return weights

  learned_when=-1
  for epoch in tqdm(range(epochs)):
    if epoch!=0:
      weights = np.copy(new_weights)

    #Forward pass:
    le_probs = get_predicted_probs(weights, v, ur, ur2datum)

    #Weight the td_probs, based on what we know about the
    #different hidden structures:
    sr2totalLEProb = {form:sum(le_probs[sr2datum[form]]) for form in sr2datum.keys()} #Sums expected SR probs (merging different HR's)
    sr2totalTDProb = {form:sum(td_probs[sr2datum[form]]) for form in sr2datum.keys()} #Sums remaining data SR probs (merging different HR's)
    weighted_tdProbs = []
    for datum_index, le_p in enumerate(le_probs):
      if sr2totalLEProb[DATA[datum_index]]==0.0:
            #exit("Got a zero when you didn't want one!")
        HR_givenSR = 0.0
      else:
        HR_givenSR = le_p/sr2totalLEProb[DATA[datum_index]] #How likely is the HRdata, given our current grammar
      weighted_tdProbs.append(HR_givenSR * sr2totalTDProb[DATA[datum_index]]) #Weight the HR probs in the training data by our current estimation of HR probs

    #Backward pass:
    TD = v.T.dot(weighted_tdProbs) #Violations present in the training data
    LE = v.T.dot(le_probs) #Violations expected by the learner
    gradients = (TD - LE)

    #Update weights:
    updates = gradients * eta
    new_weights = weights + updates

    #Police negative weights:
    if not neg_weights:
      new_weights = np.maximum(new_weights, 0)

    # # check learned yet?
    if check_learning(data, new_weights):
      learned_when = epoch+1 # epoch starts from 0 so, add 1 to be non-pythonic
      break # stop learning once learned
    else: # continue with learning if not yet learned
      pass

  return new_weights, learned_when

####################################################
# Solving fns
####################################################

def add_tableau(data, LP, udl, winner, DictOfCons, alpha):
  # generate candidates based on the UR given
  if 'HR' in data.columns:
    cands = full_cands(data, udl)
  else:
    cands = gen_SR(data, udl)

  # find the index of the winner
  for i in range(len(cands)):
    # print(i, '\n', str(cands[i]), '?== \n', str(winner))
    if str(cands[i]) == str(winner):
      # print("I found my winner", i)
      winner_id = i
      break

  # constraint names
  ListOfConNames = get_constraint_names(data)
  # make the violvec here using the cands
  violvec = evaluate_SRs(data, cands)

  # loop through the candidates
  for loser_id in range(len(cands)):
    # skipping the winner id, put loser candidate on the left side
    # put winner candidate on the right side for each loser candidate
    if loser_id != winner_id:
      LP += (
          # losing side: lpSum does sum product
          lpSum([violvec[loser_id][ListOfConNames.index(i)] * DictOfCons[i] for i in ListOfConNames])
          >=
          # winning side (margin of separation (alpha) = 1 by default)
          alpha + lpSum([violvec[winner_id][ListOfConNames.index(i)] * DictOfCons[i] for i in ListOfConNames])

          # , convert2brandon(winner) + " vs " + convert2brandon(cands[loser_id])
      )
  return LP

def solve_language(data):
  UDLs = gen_URlist(data)
  winners = get_winners(data)
  ListOfConNames = get_constraint_names(data)
  DictOfCons = LpVariable.dicts("con", ListOfConNames, lowBound=0 # no neg weights
                            # , cat='Continuous' # float weights
                            , cat='Integer' # only integer weights allowed
                            )

  if 'HR' in data.columns: # then do the branching stuff as below:
    # document how this branching is done:
    FIRST = True
    Combo = []
    solutions = []

    for i in tqdm(range(len(UDLs))):
      if FIRST: # adding tableau for UR1 (First)
        cur_UR = UDLs[i]
        # print('UR: ', cur_UR)

        winner_SR = winners[i]
        # print(f'Trying to make {winner_SR} optimal')

        consistent_HRs = gen_HR(data, winner_SR)
        # print(f'There are {len(consistent_HRs)} HRs consistent with that winner SR')
        
        # go through the consistent HRs
        for hid in consistent_HRs:
          prob = LpProblem('',LpMinimize)
          prob = add_tableau(data, prob, cur_UR, hid, DictOfCons, alpha=1)
          prob += lpSum(DictOfCons)
          if prob.solve()==1:
            Combo.append([hid])
            
            if i == len(UDLs)-1:
              w_vec = []
              for var in DictOfCons.values():
                w_vec.append(var.value())
              solutions.append(w_vec)
        # print('current number of Combos:', len(Combo))
        
        if len(Combo)==0:
          # print('Not representable')
          break
        # for branch in Combo:
        #   print(branch)
        FIRST = False

      else:
        # print('moving on to the next tableau')

        cur_UR = UDLs[i]
        # print('adding UR: ', convert2brandon(cur_UR, 'UR'))

        winner_SR = winners[i]
        # print(f'Trying to make {convert2brandon(winner_SR)} jointly optimal w/ the previous winner(s)')

        consistent_HRs = gen_HR(data, winner_SR)
        # print(f'There are {len(consistent_HRs)} HRs consistent with that winner SR')

        # take each of the stored branch and extend it by trying all the combinations:
        Updated = []
        for branch in Combo:
          for hid in consistent_HRs:
            # print('trying to add', hid)
            prob = LpProblem('',LpMinimize)
            prob = add_tableau(data, prob, cur_UR, hid, DictOfCons, alpha=1)
            for stored_hr in branch:
              # get the UR of this stored_hr
              UR_of_stored_hr = convertXtoY(data, 'HR', stored_hr, 'UR')
              prob = add_tableau(data, prob, UR_of_stored_hr, stored_hr, DictOfCons, alpha=1)

            # for constr in constraints:
            #   prob += (con_vars[constr]>=0, constr)
            prob += lpSum(DictOfCons)

            if prob.solve()==1:
              # print("succeeded, storing")
              extended_branch = branch + [hid]
              Updated.append(extended_branch)
              if i == len(UDLs)-1:
                w_vec = []
                for var in DictOfCons.values():
                  w_vec.append(var.value())
                solutions.append(w_vec)
          Combo = Updated
        # print('current number of Combos:', len(Combo))
        if len(Combo)==0:
          # print('Not representable')
          break
        # for branch in Combo:
        #   print(branch)
    print(f"Number of solutions found: {len(Combo)}")
    return solutions

  else: # no HR
    solutions= []
    prob = LpProblem('', LpMinimize)

    for tab in range(len(UDLs)):
      prob = add_tableau(data, prob, UDLs[tab], winners[tab], DictOfCons, alpha=1)
    prob += lpSum(DictOfCons)

    if prob.solve() == 1:
      w_vec = []
      for var in DictOfCons.values():
        w_vec.append(var.value())
      solutions.append(w_vec)
    else:
      print("no solution :(")
    return solutions

####################################################
# Checking results fns
####################################################

def check_found_weights(data, cands, w_vec):
  viol_vec = -1*evaluate_SRs(data, cands)
  winner_id = viol_vec.dot(w_vec).argmax()
  return cands[winner_id]

def check_solution(data, w_vec):
  UDLs = gen_URlist(data)
  observed = get_winners(data)

  CONSISTENT = True
  winners_by_found_weights = []
  if 'HR' in data.columns:
    for i in range(len(UDLs)):
      cands = full_cands(data, UDLs[i])
      winner_by_found_weights = check_found_weights(data, cands, w_vec)
      winner_by_found_weights_converted = convertXtoY(data, 'HR', winner_by_found_weights, 'SR')
      winners_by_found_weights.append(winner_by_found_weights)

      # print(winner_by_found_weights, observed[i])

      if winner_by_found_weights_converted != observed[i]:
        CONSISTENT = False
        print(f"Wrong winner by found weights for {UDLs[i]}")
        print(f"Observed: {observed[i]}")
        print(f"Found: {winner_by_found_weights_converted}")
        return 'Something Wrong :('
    if CONSISTENT:
      # print("all correct!")
      return winners_by_found_weights
  else:
    for i in range(len(UDLs)):
      cands = gen_SR(data, UDLs[i])
      winner_by_found_weights = check_found_weights(data, cands, w_vec)
      winners_by_found_weights.append(winner_by_found_weights)

      # print(winner_by_found_weights, observed[i])

      if winner_by_found_weights != observed[i]:
        CONSISTENT = False
        print(f"Wrong winner by found weights for {UDLs[i]}")
        print(f"Observed: {observed[i]}")
        print(f"Wrong: {winner_by_found_weights}")
        return 'Something Wrong :('
    if CONSISTENT:
      return winners_by_found_weights

def check_learned_weights(data, w_vec, learned_when):
  '''
  given a language and a list of weight vectors, wheter the learning is successful (learned when),
  (and URlist, and CONSTRAINTS)
  for each UR
  if successful,
  then return the top candidates with their probs,
    if the top candidate doesn't have .90 prob,
    then return the second best together
  if not successful,
    then return the observed winner and the top 1 candidate with their probs
  '''
  UDLs = gen_URlist(data)
  observed = get_winners(data)

  result = []
  for i in range(len(UDLs)):
    cur_UR = UDLs[i] # loop through each UR
    if 'HR' in data.columns:
      candidates = full_cands(data, cur_UR)
      surfaces = [convertXtoY(data, 'HR', form, 'SR') for form in candidates]
    else:
      candidates = gen_SR(data, cur_UR)
      surfaces = gen_SR(data, cur_UR)

    viol_vec = -1*evaluate_SRs(data, candidates)
    harmonies = viol_vec.dot(w_vec)
    eharmonies = np.exp(harmonies)
    Z = sum(eharmonies)
    probs = eharmonies/Z
    probs = np.array(probs)

    # choosing three best
    # ref: https://stackoverflow.com/questions/6910641/how-do-i-get-indices-of-n-maximum-values-in-a-numpy-array
    best_ids = np.argpartition(probs, -2)[-2:]
    best_ids = best_ids[np.argsort(probs[best_ids])][::-1]

    winner_ids = []
    cur_winner = observed[i]
    for id, sfc in enumerate(surfaces):
      if sfc==cur_winner:
        winner_ids.append(id)
    winner_ids = np.array(winner_ids)
    # sort winner_ids by probs
    winner_ids = winner_ids[np.argsort(probs[winner_ids])][::-1]

    if learned_when < 0: #not learned
      result.append(
          (learned_when
          , cur_winner # what shouldve been the winner
          , sum(probs[winner_ids]) # how much probs does that winner SR got
          , [candidates[i] for i in best_ids] # what are the two best candidates with current weights
          , [probs[i] for i in best_ids]) # what are the probs of those two best candidates
      )
    elif learned_when > 0: # learned
      result.append(
          (learned_when
          , cur_winner # what shouldve been the winner
          , sum(probs[winner_ids]) # how much probs does that winner SR got
          , [candidates[i] for i in winner_ids[:2]] # what are the two best HRs for that winner SR
          , [probs[i] for i in winner_ids[:2]]) # what are the probs of those two best HRs
      )
  return result

####################################################
# Printing results fns
####################################################

def print_result_pretty(data, w_vec, learned_when, outputfilename):
  RES = check_learned_weights(data, w_vec, learned_when)

  ListOfConNames = get_constraint_names(data)
  output_file_name = outputfilename+"_BriefOutput.txt"

  output_file = open(path.join("./", output_file_name), "w")

  w_vec_sorted, CON_names_sorted = (list(t) for t in zip(*sorted(zip(w_vec, ListOfConNames), reverse=True)))
  for i in range(len(CON_names_sorted)):
    line = CON_names_sorted[i] + ': ' + '%.3f'%w_vec_sorted[i]
    output_file.write(line)
    output_file.write('\n')
  output_file.write('\n')
  output_file.write('------------------------------------------')
  output_file.write('\n')

  success = RES[0][0]

  if 'HR' in data.columns:
    if success>0:
      line = f"learning was successful! language {outputfilename} learned in {success} epoch(s)"
      output_file.write(line)
      output_file.write('\n')
      for tab in RES:
        output_file.write('------------------------------------------')
        output_file.write('\n')
        line = f"observerd form {tab[1]}"+': %.2f'%tab[2]
        output_file.write(line)
        output_file.write('\n')

        output_file.write("for this SR...")
        output_file.write('\n')
        line = f"Best HR {tab[3][0]}"+': %.2f'%tab[4][0]
        output_file.write(line)
        output_file.write('\n')

    else:
      output_file.write("learning was not successful :(")
      output_file.write('\n')
      for tab in RES:
        output_file.write('------------------------------------------')
        output_file.write('\n')
        line = f"observerd form {tab[1]}"+': %.2f'%tab[2]
        output_file.write(line)
        output_file.write('\n')

        line = f"Best HR {tab[3][0]}"+': %.2f'%tab[4][0]
        output_file.write(line)
        output_file.write('\n')

  else:
    if success>0:
      line = f"learning was successful! language {outputfilename} learned in {success} epoch(s)"
      output_file.write(line)
      output_file.write('\n')
      for tab in RES:
        output_file.write('------------------------------------------')
        output_file.write('\n')
        line = f"observerd form {tab[1]}"+': %.2f'%tab[2]
        output_file.write(line)
        output_file.write('\n')
    else:
      output_file.write(f"learning was not successful :(")
      output_file.write('\n')

      for tab in RES:
        output_file.write('------------------------------------------')
        output_file.write('\n')
        line = f"observerd form {tab[1]}"+': %.2f'%tab[2]
        output_file.write(line)
        output_file.write('\n')

        output_file.write("Instead...")
        output_file.write('\n')
        line=f"Best candidate {tab[3][0]}"+': %.2f'%tab[4][0]
        output_file.write(line)
        output_file.write('\n')
  files.download(output_file_name)
  output_file.close()

def print_solutions_pretty(data, ListOfSolutions, outputfilename):
  ListOfConNames = get_constraint_names(data)
  UDLs = gen_URlist(data)
  output_file_name = outputfilename+"_all_solutions.txt"
  output_file = open(path.join("./", output_file_name), "w")
  output_file.write(f'There are {len(ListOfSolutions)} solution(s) found for {outputfilename}')
  output_file.write('\n')
  for solution in ListOfSolutions:
    output_file.write('------------------------------------------')
    output_file.write('\n')

    w_vec_sorted, CON_names_sorted = (list(t) for t in zip(*sorted(zip(solution, ListOfConNames), reverse=True)))
    for i in range(len(CON_names_sorted)):
      line = CON_names_sorted[i] + ': ' + '%.3f'%w_vec_sorted[i]
      output_file.write(line)
      output_file.write('\n')
    output_file.write('\n')

    found_winners = check_solution(data, solution)
    for winner_candidate in found_winners:
      output_file.write(winner_candidate)
      output_file.write('\n')
  files.download(output_file_name)
  output_file.close()
 
def HR_tableau(data, cur_udl, weights, comparative, sorted):
  header = ['UR', 'SR', 'HR', 'Obs', 'p']
  ListOfConNames = get_constraint_names(data)
  header += ListOfConNames
  header += ['H']

  winners = get_winners(data)
  candidates = full_cands(data, cur_udl)
  viol_mat = -1*evaluate_SRs(data, candidates)
  harmonies = viol_mat.dot(weights)
  eharmonies = np.exp(harmonies)
  Z=sum(eharmonies)
  probs=eharmonies/Z

  TableauRows = []
  id = 0
  for cand in candidates:
    row = []
    row.append(cur_udl) # ur
    sr = convertXtoY(data, 'HR', cand, 'SR')
    row.append(sr) # sr
    row.append(cand) # hr
    if sr in winners:
      row.append(1) # observed
    else:
      row.append(0)
    
    row.append(probs[id])
    row.extend(viol_mat[id])
    row.append(harmonies[id])
    TableauRows.append(row)
    id+=1
  tableau = pd.DataFrame(TableauRows, columns = header)
  if sorted:
    tableau.sort_values(by="p", ascending=False, inplace=True, ignore_index=True)
  tableau = tableau.round(2)
  if not comparative:
    return tableau
  else:
    TableauRows_comparative = []
    optimal_H = tableau.iloc[0]['H']
    optimal_p = tableau.iloc[0]['p']
    id = 0
    FIRST = True
    for r in range(len(tableau)):
      c_row = []
      c_row.append(tableau.iloc[r]['UR']) # ur
      c_row.append(tableau.iloc[r]['SR']) # sr
      c_row.append(tableau.iloc[r]['HR']) # hr
      c_row.append(tableau.iloc[r]['Obs']) # obs
      if FIRST:
        c_row.append(tableau.iloc[r]['p'])
      else:
        c_row.append(tableau.iloc[r]['p']-optimal_p)
      v = tableau.iloc[r][ListOfConNames]*weights
      c_row.extend(v)
      if FIRST:
        c_row.append(tableau.iloc[r]['H'])
      else:
        c_row.append(tableau.iloc[r]['H']-optimal_H)
      TableauRows_comparative.append(c_row)
      FIRST=False
      id+=1
    c_tableau = pd.DataFrame(TableauRows_comparative, columns = header)
    if sorted:
      c_tableau.sort_values(by="p", ascending=False, inplace=True, ignore_index=True)
    c_tableau = c_tableau.round(2)
    return c_tableau

def tableau(data, cur_udl, weights, comparative, sorted):
  header = ['UR', 'SR', 'Obs', 'p']
  ListOfConNames = get_constraint_names(data)
  header += ListOfConNames
  header += ['H']

  winners = get_winners(data)
  candidates = gen_SR(data, cur_udl)
  viol_mat = -1*evaluate_SRs(data, candidates)
  harmonies = viol_mat.dot(weights)
  eharmonies = np.exp(harmonies)
  Z=sum(eharmonies)
  probs=eharmonies/Z

  TableauRows = []
  id = 0
  for cand in candidates:
    row = []
    row.append(cur_udl) # ur
    row.append(cand) # sr
    if cand in winners:
      row.append(1) # observed
    else:
      row.append(0)
    row.append(probs[id])
    row.extend(viol_mat[id])
    row.append(harmonies[id])
    TableauRows.append(row)
    id+=1
  tableau = pd.DataFrame(TableauRows, columns = header)
  if sorted:
    tableau.sort_values(by="p", ascending=False, inplace=True, ignore_index=True)
  tableau = tableau.round(2)
  if not comparative:
    return tableau
  else:
    TableauRows_comparative = []
    optimal_H = tableau.iloc[0]['H']
    optimal_p = tableau.iloc[0]['p']
    id = 0
    FIRST = True
    for r in range(len(tableau)):
      c_row = []
      c_row.append(tableau.iloc[r]['UR']) # ur
      c_row.append(tableau.iloc[r]['SR']) # sr
      c_row.append(tableau.iloc[r]['Obs']) # obs
      if FIRST:
        c_row.append(tableau.iloc[r]['p'])
      else:
        c_row.append(tableau.iloc[r]['p']-optimal_p)
      v = tableau.iloc[r][ListOfConNames]*weights
      c_row.extend(v)
      if FIRST:
        c_row.append(tableau.iloc[r]['H'])
      else:
        c_row.append(tableau.iloc[r]['H']-optimal_H)
        
      TableauRows_comparative.append(c_row)
      FIRST=False
      id+=1
    c_tableau = pd.DataFrame(TableauRows_comparative, columns = header)
    if sorted:
      c_tableau.sort_values(by="p", ascending=False, inplace=True, ignore_index=True)
    c_tableau = c_tableau.round(2)
    return c_tableau
    
def tidy_tableaux(tableaux):
  new_tableaux = tableaux.copy()
  new_tableaux['UR'] = new_tableaux['UR'].drop_duplicates()
  new_tableaux['SR'] = new_tableaux['SR'].drop_duplicates()
  new_tableaux = new_tableaux.replace(np.nan, '-')
  return new_tableaux
  
def print_tableaux_pretty(data, weights, comparative, sorted, outputfilename):
  if 'HR' in data.columns:
    header = ['UR', 'SR', 'Obs', 'p', 'HR']
  else:
    header = ['UR', 'SR', 'Obs', 'p']
  ListOfConNames = get_constraint_names(data)
  header += ListOfConNames
  header += ['H']
  UDLs = gen_URlist(data)
  if comparative:
    isComparative = '_comparative'
  else:
    isComparative = ''
  if sorted:
    isSorted = '_sorted'
  else:
    isSorted = ''
  if comparative and sorted==False:
    return "please set 'sorted' to be True, if you want a comparative tableau"

  FIRST = True
  for ur in UDLs:
    if 'HR' in data.columns:
      cur_tab = HR_tableau(data, ur, weights, comparative, sorted)
    else:
      cur_tab = tableau(data, ur, weights, comparative, sorted)

    if FIRST:
      tab = cur_tab
      FIRST = False
    else:
      tab = pd.concat([tab, cur_tab]).reset_index(drop=True)
  if 'HR' in data.columns:
    weights = [None]*5+list(weights)+[None]
  else:
    weights = [None]*4+list(weights)+[None]
  tab.loc[-1] =  weights
  tab.index = tab.index + 1
  tab.sort_index(inplace=True)
  tab = tab.round(2)

  output_file_name = outputfilename+isComparative+isSorted+'_output_tableaux.csv'
  if sorted==False:
    tab = tidy_tableaux(tab)
    
  tab.to_csv(output_file_name, index=False)
  files.download(output_file_name)
  return tab
