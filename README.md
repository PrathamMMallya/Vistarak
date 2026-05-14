# Step 1: Stash with untracked files
git stash -u 
#this deletes temporaly

# Step 2: Pull friend's changes
git pull origin Edu_platform

# Step 3: Restore your work
git stash pop
#this brings back deleted data 

# Step 4: Setup LFS (if needed)
git lfs track "*.pth"
git add .gitattributes

# Step 5: Add ONLY your tutorial18 folder
git add tutorial/tutorial18-welcome_to_lab/

# Step 6: Verify what you're committing
git status

# Step 7: Commit
git commit -m "Add tutorial18 changes"

# Step 8: Push
git push origin Edu_platform


docker run -d \
  --name sttv2 \

  -p 9003:8003 \
  -p 9004:8004 \
  final_imageo
